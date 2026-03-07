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
    
    /* 隐藏顶部红线和默认菜单 */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    /* ---------------------------------------------------
       【核心修复】绝对显眼的侧边栏高亮与交互
       --------------------------------------------------- */
    [data-testid="stSidebar"] {
        background-color: #0f141e !important;
        border-right: 1px solid #1e293b;
    }
    
    /* 隐藏 Radio 默认圆圈 */
    .stRadio div[role="radiogroup"] > label > div:first-child { display: none !important; }
    
    /* 菜单基础样式 */
    .stRadio div[role="radiogroup"] > label {
        padding: 14px 20px !important;
        margin-bottom: 8px !important;
        border-radius: 6px !important;
        background-color: transparent !important;
        border-left: 4px solid transparent !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }
    .stRadio div[role="radiogroup"] > label p {
        font-size: 16px !important;
        color: #64748b !important;
        font-weight: 500 !important;
    }
    
    /* 菜单悬停效果 */
    .stRadio div[role="radiogroup"] > label:hover {
        background-color: rgba(0, 242, 254, 0.05) !important;
        transform: translateX(4px);
    }
    
    /* 【高亮核心】选中状态样式 (霓虹青色包围) */
    .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(90deg, rgba(0, 242, 254, 0.15) 0%, transparent 100%) !important;
        border-left: 4px solid #00f2fe !important; /* 左侧高亮青色竖线 */
        box-shadow: inset 0 0 15px rgba(0, 242, 254, 0.05) !important;
    }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] p {
        color: #00f2fe !important; /* 文字变为高亮青色 */
        font-weight: 800 !important;
        text-shadow: 0 0 8px rgba(0, 242, 254, 0.4) !important;
    }

    /* ---------------------------------------------------
       数据卡片与图表容器高级质感
       --------------------------------------------------- */
    div[data-testid="metric-container"] {
        background: rgba(16, 24, 39, 0.7);
        border: 1px solid #1e293b;
        border-top: 2px solid #00f2fe;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        letter-spacing: 1px;
    }
    div[data-testid="stMetricDelta"] svg {
        fill: #00f2fe;
    }
    
    /* 标题样式 */
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
    h4 { color: #00f2fe !important; }

    /* 表格透明化处理 */
    .dataframe { background: transparent !important; color: #c0ccda !important;}
    
    /* 标签颜色定义 */
    .badge-red { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid #ef4444; padding: 2px 8px; border-radius: 4px;}
    .badge-yellow { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid #f59e0b; padding: 2px 8px; border-radius: 4px;}
    .badge-green { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid #10b981; padding: 2px 8px; border-radius: 4px;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 会话状态与底层高保真数据流生成
# ==========================================
if "is_login" not in st.session_state:
    st.session_state.is_login = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "seed_offset" not in st.session_state:
    st.session_state.seed_offset = 0

USERS = {
    "admin": {"pwd": "1", "name": "Clay", "role": "Super Admin", "avatar": "🪐", "location": "哈尔滨云端控制中心"},
    "crew": {"pwd": "1", "name": "张伟", "role": "轮机长", "avatar": "⚓", "location": "远洋开拓号 (Voyager 01)"}
}

# 舰船静态 GIS 坐标 (用于 3D 轨迹和地图展示)
SHIP_GEO = {
    "远洋开拓号 (Voyager 01)": {"lat": 18.2, "lon": 110.5, "route": "南海航线"},
    "深蓝探索号 (Deep Blue)": {"lat": 30.1, "lon": 125.3, "route": "东海作业区"},
    "极地破冰者 (Icebreaker X)": {"lat": 65.4, "lon": -15.2, "route": "北极航线"}
}
SHIPS = list(SHIP_GEO.keys())

def generate_global_data():
    """生成具备极高仿真度的底层数据库，支持各页面的复杂调用"""
    np.random.seed(42 + st.session_state.seed_offset)
    
    # 1. 船员终端库 (150人)
    crew_list = []
    names = ["李强", "王海", "张伟", "刘洋", "陈冬", "赵钱", "孙理", "周伯通", "吴彦", "郑飞", "林峰", "萧炎"]
    for i in range(150):
        ship_name = np.random.choice(SHIPS)
        age = np.random.randint(22, 58)
        base_hr = np.random.randint(60, 85)
        crew_list.append({
            "uid": f"CRW-{202600+i}",
            "name": names[i % len(names)] + str(i//len(names) if i >= len(names) else ""),
            "ship": ship_name,
            "lat": SHIP_GEO[ship_name]["lat"] + np.random.uniform(-0.1, 0.1), # 制造船员在船上的微小分布
            "lon": SHIP_GEO[ship_name]["lon"] + np.random.uniform(-0.1, 0.1),
            "age": age,
            "mac": f"00:1A:2B:3C:{np.random.randint(10,99):02d}:{np.random.randint(10,99):02d}",
            "hr": base_hr + np.random.randint(-10, 25), # 实时心率
            "spo2": np.random.choice([99, 98, 97, 95, 92], p=[0.4, 0.3, 0.2, 0.08, 0.02]),
            "sys": 115 + (age - 20)//2 + np.random.randint(-5, 20),
            "dia": 75 + np.random.randint(-5, 15),
            "temp": round(np.random.uniform(36.1, 37.5), 1),
            "status": np.random.choice(["🟢 在线", "🟡 节能模式", "🔴 离线"], p=[0.85, 0.10, 0.05]),
            "battery": np.random.randint(2, 100),
            "network": np.random.choice(["海事卫星", "船载WiFi", "4G", "蓝牙直连"])
        })
    df_crew = pd.DataFrame(crew_list)

    # 2. 预警日志库 (300条历史+实时数据)
    alerts = []
    now = datetime.now()
    types = ["心率飙升 (>120)", "血压异常临界", "血氧跌破95%", "深度疲劳警告", "心电图(ECG)异动"]
    for i in range(300):
        lvl = np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])
        time_val = now - timedelta(minutes=np.random.randint(1, 10080)) # 过去7天
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

    # 核心指标四宫格
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("全球活跃节点", f"{len(df_crew)} 个", "网络延时 18ms")
    c2.metric("当前最高危船只", "深蓝探索号", "综合风险评分 82")
    c3.metric("待处理重度预警", str(len(df_alerts[(df_alerts['level']==3) & (df_alerts['status']=='未处理')])), "-3 起处理完毕", delta_color="inverse")
    c4.metric("云端算力负载", "42.8%", "CNN-BiLSTM 运行中")

    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([7, 3])
    with col1:
        st.markdown("#### 🗺️ 全球舰队实时生理状态 GIS 监控矩阵")
        # 【全新视觉】使用 Plotly 高逼格的深色地理散点图展示船员状态分布
        fig_map = px.scatter_mapbox(
            df_crew, lat="lat", lon="lon", color="hr", size="sys",
            hover_name="name", hover_data=["ship", "hr", "spo2", "status"],
            color_continuous_scale="Turbo", size_max=15, zoom=2,
            mapbox_style="carto-darkmatter", title="终端实时空间分布与心率热力映射"
        )
        fig_map.update_layout(
            margin=dict(l=0, r=0, t=40, b=0), paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#c0ccda"), height=450
        )
        st.plotly_chart(fig_map, use_container_width=True, key="global_map")

    with col2:
        st.markdown("#### 📊 各舰健康防线雷达对比")
        # 提取各船平均分并绘制雷达图
        radar_df = df_crew.groupby('ship').agg({'hr': 'mean', 'spo2': 'mean', 'sys': 'mean'}).reset_index()
        fig_radar = go.Figure()
        for i, row in radar_df.iterrows():
            fig_radar.add_trace(go.Scatterpolar(
                r=[row['hr'], row['spo2']*1.5, row['sys']*0.8, row['hr']], # 缩放以匹配雷达轴
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
    with col_sel:
        target_ship = st.selectbox("🎯 锁定目标作业舰", ["全舰队巡航"] + SHIPS)
    with col_btn:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("📡 强制下发采集指令", type="primary", use_container_width=True):
            st.session_state.seed_offset += 1
            st.rerun()
            
    if target_ship != "全舰队巡航":
        df_crew = df_crew[df_crew['ship'] == target_ship]

    st.markdown("#### 🔍 高危作业人员重点仪表追踪 (Top 6)")
    # 【Bug 修复】为每一个循环里的图表加上绝对唯一的 key
    sample = df_crew.head(6)
    
    for i in range(0, 6, 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(sample):
                person = sample.iloc[i + j]
                with cols[j]:
                    st.markdown(f"<div style='background:rgba(16,24,39,0.8); border:1px solid #1e293b; border-radius:8px; padding:15px;'>"
                                f"<h4 style='margin:0; text-align:center;'>{person['name']} <span style='font-size:12px;color:#64748b;'>{person['uid']}</span></h4>", 
                                unsafe_allow_html=True)
                    
                    fig = go.Figure()
                    # 心率仪表
                    fig.add_trace(go.Indicator(
                        mode="gauge+number", value=person['hr'], title={'text': "BPM", 'font': {'size': 12, 'color': '#64748b'}},
                        domain={'x': [0, 0.45], 'y': [0, 1]},
                        gauge={'axis': {'range': [40, 180], 'tickwidth': 1, 'tickcolor': "white"},
                               'bar': {'color': "#00f2fe"}, 'bgcolor': "rgba(0,0,0,0)",
                               'steps': [{'range': [100, 180], 'color': "rgba(239,68,68,0.3)"}]}
                    ))
                    # 血氧仪表
                    fig.add_trace(go.Indicator(
                        mode="gauge+number", value=person['spo2'], title={'text': "SpO2%", 'font': {'size': 12, 'color': '#64748b'}},
                        domain={'x': [0.55, 1], 'y': [0, 1]},
                        gauge={'axis': {'range': [80, 100], 'tickwidth': 1, 'tickcolor': "white"},
                               'bar': {'color': "#10b981"}, 'bgcolor': "rgba(0,0,0,0)",
                               'steps': [{'range': [80, 95], 'color': "rgba(245,158,11,0.3)"}]}
                    ))
                    fig.update_layout(height=180, margin=dict(t=20, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ffffff"))
                    # 极其关键的 key，用工号+索引绝对防撞
                    st.plotly_chart(fig, use_container_width=True, key=f"gauge_{person['uid']}_{i}_{j}")
                    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("#### 📜 全量实时监测切片 (Data Slice)")
    st.dataframe(
        df_crew[['uid', 'name', 'ship', 'hr', 'sys', 'dia', 'spo2', 'temp', 'status']].style.applymap(
            lambda x: 'color: #ef4444; font-weight: bold;' if isinstance(x, (int, float)) and (x > 120 or (80 < x < 95)) else '', 
            subset=['hr', 'spo2']
        ), height=350, use_container_width=True
    )

def render_alert_center(df_alerts):
    st.markdown("<h2>⚠️ 智能分级预警总站 (Alert Center)</h2>", unsafe_allow_html=True)
    st.caption("依托流式计算与边缘计算，实现异常指标微秒级捕捉与阻断")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### 🌌 3D 时空预警聚类分析")
        # 【全新视觉】使用 3D 散点图展示报警分布，极致的科技感
        df_3d = df_alerts.head(100).copy()
        df_3d['time_num'] = (df_3d['timestamp'] - df_3d['timestamp'].min()).dt.total_seconds()
        
        fig_3d = px.scatter_3d(
            df_3d, x='time_num', y='level', z='ship', color='level',
            symbol='status', size_max=10, opacity=0.8,
            color_continuous_scale=['#10b981', '#f59e0b', '#ef4444'],
            labels={'time_num': '时间轴(偏移)', 'level': '严重等级', 'ship': '源节点'},
            title="预警事件三维空间散布图"
        )
        fig_3d.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", 
            scene=dict(xaxis=dict(showticklabels=False), bgcolor="rgba(10,14,23,0.5)"),
            margin=dict(l=0, r=0, b=0, t=30), height=450
        )
        st.plotly_chart(fig_3d, use_container_width=True, key="3d_alert_scatter")
        
    with col2:
        st.markdown("#### 🚨 实时高危事件响应队列")
        # 美化表格展示
        df_show = df_alerts[['time_str', 'crew', 'ship', 'type', 'level', 'status']].head(15).copy()
        
        # 赋予 HTML 颜色标签 (在 Streamlit 中直接使用 HTML 需要特定设置，这里用 Pandas Style 替代)
        def style_level(val):
            if val == 3: return 'background-color: rgba(239,68,68,0.2); color: #ef4444;'
            elif val == 2: return 'background-color: rgba(245,158,11,0.2); color: #f59e0b;'
            return 'background-color: rgba(16,185,129,0.2); color: #10b981;'
            
        st.dataframe(
            df_show.style.applymap(style_level, subset=['level']).applymap(
                lambda x: 'color: #ef4444; font-weight:bold;' if x == '未处理' else 'color: #64748b;', subset=['status']
            ), height=450, use_container_width=True
        )

def render_ai_engine():
    st.markdown("<h2>🧠 CNN-BiLSTM 算法中枢 (AI Core)</h2>", unsafe_allow_html=True)
    st.caption("基于深度神经网络的特征提取与序列预测，突破传统静态阈值盲区")
    
    st.info("⚡ **引擎内核状态**：活跃运行中 | 神经网络层数：12 层 | 历史训练样本：4.2 TB PPG 信号")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("#### 📉 运动伪影剔除与信号重建演示")
        # 模拟深度学习清洗信号前后的对比图
        t = np.linspace(0, 10, 200)
        clean_ecg = np.sin(2 * np.pi * 1.5 * t) + 0.5 * np.sin(2 * np.pi * 3 * t) # 模拟基线ECG
        noise = np.random.normal(0, 0.8, 200) * np.sin(2 * np.pi * 0.1 * t) # 模拟大范围运动干扰
        
        fig_sig = go.Figure()
        fig_sig.add_trace(go.Scatter(x=t, y=clean_ecg + noise, name='原始受损信号 (含运动伪影)', line=dict(color='rgba(239,68,68,0.6)')))
        fig_sig.add_trace(go.Scatter(x=t, y=clean_ecg, name='AI 重建纯净波形', line=dict(color='#00f2fe', width=3)))
        fig_sig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350, legend=dict(y=1.1, orientation="h"))
        st.plotly_chart(fig_sig, use_container_width=True, key="ai_signal")
        
    with c2:
        st.markdown("#### 🌡️ 作业强度与心肺衰竭风险热力交叉分析")
        # 热力图展示关联性
        z_data = np.random.normal(loc=50, scale=15, size=(6, 5))
        z_data[4:, 3:] += 40 # 制造高风险区域
        
        fig_heat = px.imshow(
            z_data, x=['极低强度', '轻度巡检', '常规作业', '高负荷', '极限突破'],
            y=['睡眠>8h', '6-8h', '4-6h', '2-4h', '极度剥夺<2h', '连续通宵'],
            color_continuous_scale="Inferno", aspect="auto"
        )
        fig_heat.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=350)
        st.plotly_chart(fig_heat, use_container_width=True, key="ai_heatmap")

def render_device_assets(df_crew):
    st.markdown("<h2>⌚ 硬件矩阵与 OTA 控制台 (Assets & OTA)</h2>", unsafe_allow_html=True)
    st.caption("全网终端设备生命周期管理、电量监控与传输通道调度")
    
    col1, col2 = st.columns([3, 7])
    with col1:
        st.markdown("#### 🔋 全网设备状态剖析")
        # 【全新视觉】使用高级树状图 Treemap 展示设备的网络和状态层级
        tree_df = df_crew.groupby(['network', 'status']).size().reset_index(name='count')
        fig_tree = px.treemap(
            tree_df, path=['network', 'status'], values='count',
            color='status', color_discrete_map={"🟢 在线": "#10b981", "🟡 节能模式": "#f59e0b", "🔴 离线": "#ef4444"},
            title="传输信道与运行状态拓扑"
        )
        fig_tree.update_layout(margin=dict(t=30, l=0, r=0, b=0), paper_bgcolor="rgba(0,0,0,0)", height=450)
        st.plotly_chart(fig_tree, use_container_width=True, key="device_treemap")
        
    with col2:
        st.markdown("#### 📦 硬件台账明细与批量管理")
        
        # 导出 Excel 容错模块
        if st.button("📥 抽取加密 Excel 台账报表", type="primary"):
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_crew[['mac', 'uid', 'name', 'ship', 'network', 'battery', 'status']].to_excel(writer, index=False, sheet_name="手环资产")
                excel_data = output.getvalue()
                
                st.download_button("✅ 报告编译完成，点击下载 (.xlsx)", data=excel_data, file_name=f"Assets_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except ImportError:
                st.error("🚨 核心组件缺失：系统底层未检测到 `openpyxl` 驱动。")
                st.code("pip install openpyxl", language="bash")
                st.info("请在控制台执行上方指令进行极速安装，安装完毕后刷新即刻生效。")
                
        # 表格展示
        df_show = df_crew[['mac', 'name', 'ship', 'battery', 'network', 'status']].copy()
        st.dataframe(
            df_show.style.bar(subset=['battery'], color='#00f2fe', vmin=0, vmax=100),
            height=370, use_container_width=True
        )

# ==========================================
# 5. 系统主脑路由 (Router)
# ==========================================
def main():
    if not st.session_state.is_login:
        c1, c2, c3 = st.columns([1, 1.2, 1])
        with c2:
            st.markdown("<div style='margin-top:10vh;'></div>", unsafe_allow_html=True)
            st.markdown("<h1 style='text-align:center; color:#00f2fe; font-size:3.5rem; letter-spacing: 2px;'>海泰新航</h1>", unsafe_allow_html=True)
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
            
            # 使用原生 Radio，配合顶部的极客 CSS 实现完美高亮
            menus = ["📊 全局驾驶舱", "💓 终端矩阵监测", "⚠️ 预警阻断总站", "🧠 CNN-BiLSTM 引擎", "⌚ 硬件与 OTA 管理"]
            choice = st.radio("Navigation", menus, label_visibility="collapsed")
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("🚪 切断连接 (LOGOUT)", use_container_width=True):
                st.session_state.is_login = False
                st.rerun()

        # 路由分发
        if choice == menus[0]: render_dashboard(df_crew, df_alerts)
        elif choice == menus[1]: render_monitor(df_crew)
        elif choice == menus[2]: render_alert_center(df_alerts)
        elif choice == menus[3]: render_ai_engine()
        elif choice == menus[4]: render_device_assets(df_crew)

if __name__ == "__main__":
    main()  