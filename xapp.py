import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import io

# ==========================================
# 1. 页面基础配置 (全屏宽幅)
# ==========================================
st.set_page_config(
    page_title="海泰新航 - 船员生理监测云脑",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. 全新重构：Cyber-Industrial 顶级 UI/CSS
# ==========================================
st.markdown("""
<style>
    /* 全局深空背景与高亮文本 */
    .stApp {
        background-color: #0a0e17; /* 极致深空蓝黑 */
        color: #c0ccda;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    /* ---------------------------------------------------
       【核心修复 1：解决字太暗看不清的问题】
       --------------------------------------------------- */
    /* 登录框和输入框上方的标题文字 */
    .stTextInput label p, .stSelectbox label p, .stNumberInput label p {
        color: #00f2fe !important;  
        font-size: 16px !important;
        font-weight: 800 !important;
    }
    
    /* 修复输入框里面打字、下拉框选中后的文字颜色（强制纯白，加粗） */
    .stTextInput input, .stNumberInput input, div[data-baseweb="select"] span {
        color: #ffffff !important; 
        font-weight: 800 !important;
        font-size: 16px !important;
    }
    
    /* 修复占位符颜色 */
    .stTextInput input::placeholder {
        color: #cbd5e1 !important; 
        opacity: 1 !important;
    }
    
    /* 修复系统内部数据表格的表头和内容字色 */
    .dataframe th { 
        color: #00f2fe !important; 
        font-weight: 800 !important; 
        font-size: 15px !important;
    }
    .dataframe td { 
        color: #ffffff !important; /* 强制纯白 */
        font-weight: 500 !important;
        font-size: 15px !important;
    }

    /* ---------------------------------------------------
       侧边栏与数据卡片样式保持原样
       --------------------------------------------------- */
    [data-testid="stSidebar"] {
        background-color: #0f141e !important;
        border-right: 1px solid #1e293b;
    }
    .stRadio div[role="radiogroup"] > label > div:first-child { display: none !important; }
    .stRadio div[role="radiogroup"] > label {
        padding: 14px 20px !important; margin-bottom: 8px !important; border-radius: 6px !important;
        background-color: transparent !important; border-left: 4px solid transparent !important; transition: all 0.3s ease !important; cursor: pointer !important;
    }
    .stRadio div[role="radiogroup"] > label p { font-size: 16px !important; color: #64748b !important; font-weight: 500 !important; }
    .stRadio div[role="radiogroup"] > label:hover { background-color: rgba(0, 242, 254, 0.05) !important; transform: translateX(4px); }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(90deg, rgba(0, 242, 254, 0.15) 0%, transparent 100%) !important;
        border-left: 4px solid #00f2fe !important; box-shadow: inset 0 0 15px rgba(0, 242, 254, 0.05) !important;
    }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] p { color: #00f2fe !important; font-weight: 800 !important; text-shadow: 0 0 8px rgba(0, 242, 254, 0.4) !important; }

    div[data-testid="metric-container"] {
        background: rgba(16, 24, 39, 0.7); border: 1px solid #1e293b; border-top: 2px solid #00f2fe;
        border-radius: 8px; padding: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 2.2rem !important; font-weight: 700 !important; letter-spacing: 1px; }
    div[data-testid="stMetricDelta"] svg { fill: #00f2fe; }
    
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
    h4 { color: #00f2fe !important; }
    .dataframe { background: transparent !important; }
    
    .badge-red { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid #ef4444; padding: 2px 8px; border-radius: 4px;}
    .badge-yellow { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid #f59e0b; padding: 2px 8px; border-radius: 4px;}
    .badge-green { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid #10b981; padding: 2px 8px; border-radius: 4px;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 会话状态与底层高保真数据流生成
# ==========================================
if "is_login" not in st.session_state: st.session_state.is_login = False
if "user_info" not in st.session_state: st.session_state.user_info = {}
if "seed_offset" not in st.session_state: st.session_state.seed_offset = 0

USERS = {
    "admin": {"pwd": "1", "name": "Clay", "role": "Super Admin", "avatar": "🪐", "location": "哈尔滨云端控制中心"},
    "crew": {"pwd": "1", "name": "张伟", "role": "轮机长", "avatar": "⚓", "location": "远洋开拓号"}
}

# 【核心修改】：地图点位精简为 6 艘主力舰船
SHIP_GEO = {
    "远洋开拓号 (Voyager 01)": {"lat": 18.2, "lon": 110.5},
    "深蓝探索号 (Deep Blue)": {"lat": 30.1, "lon": 125.3},
    "极地破冰者 (Icebreaker X)": {"lat": 65.4, "lon": -15.2},
    "海上先锋号 (Pioneer)": {"lat": 10.5, "lon": 105.2},
    "星辰领航号 (Navigator)": {"lat": 45.1, "lon": 150.3},
    "深海巨兽号 (Leviathan)": {"lat": -10.5, "lon": 70.2}
}
SHIPS = list(SHIP_GEO.keys())

def generate_global_data():
    np.random.seed(42 + st.session_state.seed_offset)
    
    crew_list = []
    names = ["李强", "王海", "张伟", "刘洋", "陈冬", "赵钱", "孙理", "周伯通", "吴彦", "郑飞", "林峰", "萧炎"]
    for i in range(150):
        ship_name = np.random.choice(SHIPS)
        crew_list.append({
            "uid": f"CRW-{202600+i}",
            "name": names[i % len(names)] + str(i//len(names) if i >= len(names) else ""),
            "ship": ship_name,
            "lat": SHIP_GEO[ship_name]["lat"], # 锁定经纬度，不再加随机偏移
            "lon": SHIP_GEO[ship_name]["lon"],
            "age": np.random.randint(22, 58),
            "mac": f"00:1A:2B:3C:{np.random.randint(10,99):02d}:{np.random.randint(10,99):02d}",
            "hr": np.random.randint(60, 110), 
            "spo2": np.random.choice([99, 98, 97, 95, 92], p=[0.4, 0.3, 0.2, 0.08, 0.02]),
            "sys": 115 + np.random.randint(-5, 20),
            "dia": 75 + np.random.randint(-5, 15),
            "temp": round(np.random.uniform(36.1, 37.5), 1),
            "status": np.random.choice(["🟢 在线", "🟡 节能", "🔴 离线"], p=[0.85, 0.10, 0.05]),
            "battery": np.random.randint(2, 100),
            "network": np.random.choice(["海事卫星", "船载WiFi", "4G", "蓝牙直连"])
        })
    df_crew = pd.DataFrame(crew_list)

    alerts = []
    now = datetime.now()
    types = ["心率飙升 (>120)", "血压异常临界", "血氧跌破95%", "深度疲劳警告", "心电图(ECG)异动"]
    for i in range(300):
        lvl = np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])
        time_val = now - timedelta(minutes=np.random.randint(1, 10080)) 
        alerts.append({
            "alert_id": f"ALT-{np.random.randint(10000,99999)}",
            "timestamp": time_val,
            "time_str": time_val.strftime("%m-%d %H:%M:%S"),
            "ship": np.random.choice(SHIPS),
            "crew": np.random.choice(crew_list)['name'],
            "type": np.random.choice(types),
            "level": lvl,
            "status": "已处理" if np.random.random() > 0.4 else "未处理"
        })
    df_alerts = pd.DataFrame(alerts).sort_values("timestamp", ascending=False)
    return df_crew, df_alerts

# ==========================================
# 4. 核心渲染模块 (分体隔离，极致视觉)
# ==========================================

def render_dashboard(df_crew, df_alerts):
    st.markdown("<h2>🌍 舰队全局控制中枢 (Global Command)</h2>", unsafe_allow_html=True)
    st.caption("汇聚全网传感器终端，秒级吞吐海量生理指标")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("全球活跃节点", f"{len(df_crew)} 个", "网络延时 18ms")
    c2.metric("当前最高危船只", "深蓝探索号", "综合风险评分 82")
    c3.metric("待处理重度预警", str(len(df_alerts[(df_alerts['level']==3) & (df_alerts['status']=='未处理')])), "-3 起处理完毕", delta_color="inverse")
    c4.metric("云端算力负载", "42.8%", "CNN-BiLSTM 运行中")

    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([7, 3])
    with col1:
        st.markdown("#### 🗺️ 全球舰队纯离线 GIS 监控 (支持鼠标滚轮缩放与拖拽)")
        
        # 【核心重构 2：地图只有 6 个大点，纯离线不断网】
        # 先按舰船把数据聚合起来，算出每艘船的平均心率和人数
        map_df = df_crew.groupby('ship').agg({'lat':'first', 'lon':'first', 'hr':'mean', 'uid':'count'}).reset_index()
        
        fig_map = go.Figure()
        # 铺设真实舰队核心节点 (超大点 + 详细悬浮信息)
        fig_map.add_trace(go.Scattergeo(
            lat=map_df['lat'], lon=map_df['lon'], 
            mode='markers+text',
            text=map_df['ship'], textposition="top center", textfont=dict(color="#00f2fe", size=14, weight="bold"),
            marker=dict(
                size=30,  # 点位极度放大
                color=map_df['hr'], colorscale='Turbo', 
                showscale=True, colorbar=dict(title="均值心率(BPM)", tickfont=dict(color="#ffffff")),
                line=dict(width=2, color='rgba(255,255,255,0.5)')
            ),
            hovertext=map_df['ship'] + "<br>设备数: " + map_df['uid'].astype(str) + " 台<br>舱内均值心率: " + map_df['hr'].round(1).astype(str) + " BPM",
            hoverinfo='text',
            name="主力舰队"
        ))
        
        fig_map.update_geos(
            projection_type="equirectangular", showcoastlines=True, coastlinecolor="#1e293b",
            showland=True, landcolor="#0b101a", showocean=True, oceancolor="#05080f",
            showcountries=True, countrycolor="#1e293b",
            bgcolor="rgba(0,0,0,0)", center=dict(lon=110, lat=25)
        )
        fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"), height=450)
        
        # 开启 scrollZoom 交互配置
        st.plotly_chart(fig_map, use_container_width=True, key="offline_map", config={'scrollZoom': True, 'displayModeBar': True})

    with col2:
        st.markdown("#### 📊 各舰健康防线雷达对比")
        radar_df = df_crew.groupby('ship').agg({'hr': 'mean', 'spo2': 'mean', 'sys': 'mean'}).reset_index()
        fig_radar = go.Figure()
        for i, row in radar_df.iterrows():
            fig_radar.add_trace(go.Scatterpolar(
                r=[row['hr'], row['spo2']*1.5, row['sys']*0.8, row['hr']], 
                theta=['心率负荷', '供氧指数', '血压峰值', '心率负荷'],
                fill='toself', name=row['ship']
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=False), bgcolor="rgba(16,24,39,0.5)"),
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", showlegend=True,
            legend=dict(orientation="h", y=-0.2), height=450, margin=dict(t=30, b=0, l=20, r=20)
        )
        st.plotly_chart(fig_radar, use_container_width=True, key="radar_chart")

def render_monitor(df_crew):
    st.markdown("<h2>💓 终端矩阵实时监控 (Real-time Matrix)</h2>", unsafe_allow_html=True)
    col_sel, col_btn = st.columns([8, 2])
    with col_sel: target_ship = st.selectbox("🎯 锁定目标作业舰", ["全舰队巡航"] + SHIPS)
    with col_btn:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("📡 强制下发采集指令", type="primary", use_container_width=True):
            st.session_state.seed_offset += 1
            st.rerun()
            
    if target_ship != "全舰队巡航": df_crew = df_crew[df_crew['ship'] == target_ship]

    st.markdown("#### 🔍 高危作业人员重点仪表追踪 (Top 6)")
    sample = df_crew.head(6)
    for i in range(0, 6, 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(sample):
                person = sample.iloc[i + j]
                with cols[j]:
                    st.markdown(f"<div style='background:rgba(16,24,39,0.8); border:1px solid #1e293b; border-radius:8px; padding:15px;'><h4 style='margin:0; text-align:center;'>{person['name']} <span style='font-size:12px;color:#64748b;'>{person['uid']}</span></h4>", unsafe_allow_html=True)
                    fig = go.Figure()
                    fig.add_trace(go.Indicator(mode="gauge+number", value=person['hr'], title={'text': "BPM", 'font': {'color': '#64748b'}}, domain={'x': [0, 0.45], 'y': [0, 1]}, gauge={'axis': {'range': [40, 180]}, 'bar': {'color': "#00f2fe"}}))
                    fig.add_trace(go.Indicator(mode="gauge+number", value=person['spo2'], title={'text': "SpO2%", 'font': {'color': '#64748b'}}, domain={'x': [0.55, 1], 'y': [0, 1]}, gauge={'axis': {'range': [80, 100]}, 'bar': {'color': "#10b981"}}))
                    fig.update_layout(height=180, margin=dict(t=20, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"))
                    st.plotly_chart(fig, use_container_width=True, key=f"g_{person['uid']}")
                    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("#### 📜 全量实时监测切片 (Data Slice)")
    st.dataframe(df_crew[['uid', 'name', 'ship', 'hr', 'sys', 'dia', 'spo2', 'temp', 'status']].style.applymap(lambda x: 'color: #ef4444; font-weight: bold;' if isinstance(x, (int, float)) and (x > 120 or (80 < x < 95)) else '', subset=['hr', 'spo2']), height=350, use_container_width=True)

def render_alert_center(df_alerts):
    st.markdown("<h2>⚠️ 智能分级预警总站 (Alert Center)</h2>", unsafe_allow_html=True)
    st.caption("依托流式计算与边缘计算，实现异常指标微秒级捕捉与阻断")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### 🌌 3D 时空预警聚类分析")
        df_3d = df_alerts.head(100).copy()
        df_3d['time_num'] = (df_3d['timestamp'] - df_3d['timestamp'].min()).dt.total_seconds()
        fig_3d = px.scatter_3d(df_3d, x='time_num', y='level', z='ship', color='level', symbol='status', size_max=10, opacity=0.8, color_continuous_scale=['#10b981', '#f59e0b', '#ef4444'])
        fig_3d.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", scene=dict(xaxis=dict(showticklabels=False), bgcolor="rgba(10,14,23,0.5)"), margin=dict(l=0, r=0, b=0, t=30), height=450)
        st.plotly_chart(fig_3d, use_container_width=True)
        
    with col2:
        st.markdown("#### 🚨 实时高危事件响应队列")
        df_show = df_alerts[['time_str', 'crew', 'ship', 'type', 'level', 'status']].head(15).copy()
        def style_level(val):
            if val == 3: return 'background-color: rgba(239,68,68,0.2); color: #ef4444;'
            elif val == 2: return 'background-color: rgba(245,158,11,0.2); color: #f59e0b;'
            return 'background-color: rgba(16,185,129,0.2); color: #10b981;'
        st.dataframe(df_show.style.applymap(style_level, subset=['level']).applymap(lambda x: 'color: #ef4444; font-weight:bold;' if x == '未处理' else 'color: #64748b;', subset=['status']), height=450, use_container_width=True)

def render_ai_engine():
    st.markdown("<h2>🧠 CNN-BiLSTM 算法中枢 (AI Core)</h2>", unsafe_allow_html=True)
    st.caption("基于深度神经网络的特征提取与序列预测，突破传统静态阈值盲区")
    st.info("⚡ **引擎内核状态**：活跃运行中 | 神经网络层数：12 层 | 历史训练样本：4.2 TB PPG 信号")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        # 【核心修改 3.1】：直观的特征权重条形图，代替看不懂的波形
        st.markdown("#### ⚖️ 预警核心关联特征归因分析 (SHAP)")
        st.caption("实时展示导致系统报警的核心诱发因素（解释性 AI）")
        
        features = ['连续作业时长 (h)', '深度睡眠剥夺量 (h)', '心率变异性波峰 (HRV)', '血氧持续波谷', '环境温差应激反应']
        importances = [35.2, 28.5, 18.3, 12.0, 6.0]
        
        fig_shap = go.Figure(go.Bar(
            x=importances, y=features, orientation='h',
            marker=dict(color='#00f2fe', opacity=0.9)
        ))
        fig_shap.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis=dict(title="特征权重贡献度 (%)", showgrid=True, gridcolor="#1e293b"), yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_shap, use_container_width=True, key="ai_shap")
        
    with c2:
        # 【核心修改 3.2】：带预测置信区间的疲劳度预测，代替看不懂的热力图
        st.markdown("#### 📈 BiLSTM 个体疲劳负荷超前推演")
        st.caption("实线为历史采集数据，虚线及高亮阴影区为 AI 预测的未来 4 小时趋势。")
        
        hours = list(range(-12, 5)) 
        history = [40, 42, 41, 45, 48, 55, 58, 62, 60, 68, 72, 75, 78]
        future_mean = [82, 85, 89, 92]
        future_upper = [85, 90, 95, 98]
        future_lower = [79, 80, 83, 86]
        
        fig_pred = go.Figure()
        fig_pred.add_trace(go.Scatter(x=hours[:13], y=history, mode='lines+markers', name='历史真实记录', line=dict(color='#00f2fe', width=3)))
        fig_pred.add_trace(go.Scatter(x=hours[12:], y=[history[-1]] + future_mean, mode='lines', name='AI 预测中值', line=dict(color='#f59e0b', width=3, dash='dash')))
        fig_pred.add_trace(go.Scatter(
            x=hours[12:] + hours[12:][::-1], 
            y=[history[-1]] + future_upper + ([history[-1]] + future_lower)[::-1],
            fill='toself', fillcolor='rgba(245, 158, 11, 0.2)', line=dict(color='rgba(255,255,255,0)'),
            name='95% 预测范围区间'
        ))
        fig_pred.add_hline(y=85, line_dash="dash", line_color="#ef4444", annotation_text="重度疲劳阻断阈值", annotation_font_color="#ef4444")
        
        fig_pred.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350,
            margin=dict(l=10, r=10, t=20, b=10), legend=dict(orientation="h", y=-0.2),
            xaxis=dict(title="时间轴偏移 (h)", showgrid=False), yaxis=dict(title="疲劳负荷指数", gridcolor="#1e293b", range=[30, 100])
        )
        st.plotly_chart(fig_pred, use_container_width=True, key="ai_confidence")

def render_device_assets(df_crew):
    st.markdown("<h2>⌚ 硬件矩阵与 OTA 控制台 (Assets & OTA)</h2>", unsafe_allow_html=True)
    st.caption("全网终端设备生命周期管理、电量监控与传输通道调度")
    
    col1, col2 = st.columns([3, 7])
    with col1:
        # 【核心修改 4】：把硬件方块图换成了直观的环形交互图
        st.markdown("#### 📡 终端通信信道拓扑分布")
        net_df = df_crew['network'].value_counts().reset_index()
        fig_pie = px.pie(
            net_df, values='count', names='network', hole=0.6, 
            color_discrete_sequence=['#00f2fe', '#10b981', '#8b5cf6', '#f59e0b']
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"), 
            margin=dict(t=30, b=10, l=10, r=10), height=400,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_pie, use_container_width=True, key="donut_network")
        
    with col2:
        st.markdown("#### 📦 硬件台账明细与批量管理")
        if st.button("📥 抽取加密 Excel 台账报表", type="primary"):
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_crew[['mac', 'uid', 'name', 'ship', 'network', 'battery', 'status']].to_excel(writer, index=False, sheet_name="手环资产")
                excel_data = output.getvalue()
                st.download_button("✅ 报告编译完成，点击下载 (.xlsx)", data=excel_data, file_name=f"Assets_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except ImportError:
                st.error("🚨 核心组件缺失：系统底层未检测到 `openpyxl` 驱动。")
                st.code("pip install openpyxl", language="bash")
                
        df_show = df_crew[['mac', 'name', 'ship', 'battery', 'network', 'status']].copy()
        st.dataframe(df_show.style.bar(subset=['battery'], color='#00f2fe', vmin=0, vmax=100), height=370, use_container_width=True)

# ==========================================
# 5. 系统主脑路由 (Router)
# ==========================================
def main():
    if not st.session_state.is_login:
        c1, c2, c3 = st.columns([1, 1.2, 1])
        with c2:
            st.markdown("<div style='margin-top:10vh;'></div>", unsafe_allow_html=True)
            st.markdown("<h1 style='text-align:center; color:#00f2fe; font-size:3.5rem; letter-spacing: 2px;'>海泰新航 OS</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#64748b;'>多传感器数据监控平台</p><br>", unsafe_allow_html=True)
            
            with st.form("auth_form"):
                usr = st.text_input("终端操作员 ID (admin)")
                pwd = st.text_input("安全通信密钥 (1)", type="password")
                if st.form_submit_button("接入核心网络 (CONNECT)", use_container_width=True):
                    if usr in USERS and pwd == USERS[usr]['pwd']:
                        st.session_state.is_login = True
                        st.session_state.user_info = USERS[usr]
                        st.rerun()
                    else:
                        st.error("⚠️ 认证拒绝：非法的操作凭证。")
    else:
        df_crew, df_alerts = generate_global_data()
        user = st.session_state.user_info
        
        with st.sidebar:
            st.markdown(f"""
            <div style="background: rgba(16,24,39,0.5); padding: 20px; border-radius: 8px; border: 1px solid #1e293b; margin-bottom: 25px;">
                <h1 style="margin:0; font-size:40px; text-shadow: 0 0 10px rgba(0,242,254,0.5);">{user['avatar']}</h1>
                <h3 style="margin: 10px 0 5px 0; color: #ffffff;">{user['name']}</h3>
                <span style="background: rgba(0,242,254,0.2); color:#00f2fe; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">{user['role']}</span>
                <p style="margin: 10px 0 0 0; color: #64748b; font-size: 12px;">📍 {user['location']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<p style='color: #64748b; font-size: 13px; font-weight: bold; margin-bottom: 5px; letter-spacing: 1px;'>系统功能阵列</p>", unsafe_allow_html=True)
            
            menus = ["📊 全局驾驶舱", "💓 终端矩阵监测", "⚠️ 预警阻断总站", "🧠 CNN-BiLSTM 引擎", "⌚ 硬件与 OTA 管理"]
            choice = st.radio("Navigation", menus, label_visibility="collapsed")
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("🚪 切断连接 (LOGOUT)", use_container_width=True):
                st.session_state.is_login = False
                st.rerun()

        if choice == menus[0]: render_dashboard(df_crew, df_alerts)
        elif choice == menus[1]: render_monitor(df_crew)
        elif choice == menus[2]: render_alert_center(df_alerts)
        elif choice == menus[3]: render_ai_engine()
        elif choice == menus[4]: render_device_assets(df_crew)

if __name__ == "__main__":
    main()
