import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import re
from matplotlib import colors
import matplotlib as mpl

# 设置页面配置
st.set_page_config(
    page_title="化学反应速率计算器",
    page_icon="🧪",
    layout="wide"
)

# 设置matplotlib支持中文
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def parse_scientific_notation(text):
    """
    解析科学计数法
    支持格式：1.5e5, 1.5E5, 1.5×10^5, 1.5×105, 1.5*10^5等
    """
    if text is None or text == '':
        return None
    
    # 转换为字符串并去除空格
    text = str(text).strip()
    
    # 尝试直接转换（处理普通数字和标准科学计数法）
    try:
        return float(text)
    except:
        pass
    
    # 处理各种科学计数法格式
    patterns = [
        (r'([+-]?\d*\.?\d+)\s*[×xX\*]\s*10\^([+-]?\d+)', r'\1e\2'),  # 1.5×10^5
        (r'([+-]?\d*\.?\d+)\s*[×xX\*]\s*10([+-]?\d+)', r'\1e\2'),     # 1.5×105
        (r'([+-]?\d*\.?\d+)\s*[eE]\s*([+-]?\d+)', r'\1e\2'),          # 1.5e5
    ]
    
    for pattern, replacement in patterns:
        match = re.match(pattern, text)
        if match:
            try:
                result = re.sub(pattern, replacement, text)
                return float(result)
            except:
                pass
    
    # 如果都不匹配，尝试最后一次直接转换
    try:
        return float(text)
    except:
        st.error(f"无法解析数值: {text}")
        return None

def calculate_rate_constant(T, A, n, Ea, R=1.987):
    """
    计算反应速率常数
    k = A * T^n * exp(-Ea/RT)
    
    参数:
    T: 温度 (K)
    A: 指前因子
    n: 温度指数
    Ea: 活化能 (cal/mol)
    R: 理想气体常数 (1.987 cal/(mol·K))
    """
    return A * (T ** n) * np.exp(-Ea / (R * T))

def generate_color(index):
    """生成不同的颜色"""
    cmap = plt.get_cmap('tab10')
    return cmap(index % 10)

# 主界面
st.title("🧪 化学反应速率常数计算器")
st.markdown("基于Arrhenius公式: $k = AT^n e^{-E_a/RT}$")

# 创建侧边栏用于设置
with st.sidebar:
    st.header("⚙️ 设置")
    
    # 温度范围设置
    st.subheader("温度范围")
    col1, col2 = st.columns(2)
    with col1:
        T_min = st.number_input("最小温度 (K)", value=300, min_value=100, max_value=5000)
    with col2:
        T_max = st.number_input("最大温度 (K)", value=2000, min_value=100, max_value=5000)
    
    # 横轴类型选择
    st.subheader("横轴设置")
    x_axis_type = st.radio(
        "横轴类型",
        ["温度 T (K)", "1000/T (K⁻¹)"],
        help="选择横轴显示温度T或1000/T（Arrhenius图）"
    )
    
    # Y轴范围设置
    st.subheader("Y轴范围 (log₁₀(k))")
    
    # 自动或手动设置Y轴
    y_axis_mode = st.radio(
        "Y轴范围模式",
        ["自动", "手动设置"],
        help="选择自动会根据数据自动调整Y轴范围"
    )
    
    if y_axis_mode == "手动设置":
        col1, col2 = st.columns(2)
        with col1:
            y_min = st.number_input(
                "Y轴最小值", 
                value=-20.0, 
                format="%.1f",
                help="log₁₀(k)的最小值"
            )
        with col2:
            y_max = st.number_input(
                "Y轴最大值", 
                value=20.0, 
                format="%.1f",
                help="log₁₀(k)的最大值"
            )
    else:
        y_min = None
        y_max = None
    
    # 气体常数设置
    st.subheader("物理常数")
    R_value = st.number_input(
        "气体常数 R (cal/(mol·K))", 
        value=1.987,
        format="%.3f",
        help="默认值: 1.987 cal/(mol·K)" 
    )
    
    # 图表设置
    st.subheader("图表设置")
    show_grid = st.checkbox("显示网格", value=True)
    show_legend = st.checkbox("显示图例", value=True)
    line_width = st.slider("线条宽度", min_value=1, max_value=5, value=2)
    
    # 添加快速Y轴范围调整按钮
    if y_axis_mode == "手动设置":
        st.subheader("快速设置")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("燃烧反应\n(-10 到 20)"):
                y_min = -10.0
                y_max = 20.0
                st.rerun()
        with col2:
            if st.button("催化反应\n(-20 到 10)"):
                y_min = -20.0
                y_max = 10.0
                st.rerun()

# 初始化session state
if 'reactions' not in st.session_state:
    st.session_state.reactions = [
        {
            'equation': '',
            'A': '',
            'n': '',
            'Ea': '',
            'reference': ''
        }
    ]

# 主界面 - 输入区域
st.header("📝 输入反应参数")

st.markdown("""
**输入说明:**
- A: 指前因子（支持科学计数法，如 1.5e13, 1.5×10^13, 1.5×1013）
- n: 温度指数
- Ea: 活化能 (cal/mol)
- 参考文献: 数据来源
""")

# 动态创建输入行
for i, reaction in enumerate(st.session_state.reactions):
    with st.container():
        col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 1.5, 2, 2, 1, 1])
        
        with col1:
            reaction['equation'] = st.text_input(
                f"反应方程 {i+1}",
                value=reaction['equation'],
                key=f"eq_{i}",
                placeholder="如: H + O2 = OH + O"
            )
        
        with col2:
            reaction['A'] = st.text_input(
                f"A",
                value=reaction['A'],
                key=f"A_{i}",
                placeholder="1.5e13"
            )
        
        with col3:
            reaction['n'] = st.text_input(
                f"n",
                value=reaction['n'],
                key=f"n_{i}",
                placeholder="0"
            )
        
        with col4:
            reaction['Ea'] = st.text_input(
                f"Ea (cal/mol)",
                value=reaction['Ea'],
                key=f"Ea_{i}",
                placeholder="50000"
            )
        
        with col5:
            reaction['reference'] = st.text_input(
                f"参考文献",
                value=reaction['reference'],
                key=f"ref_{i}",
                placeholder="Smith 2020"
            )
        
        with col6:
            if st.button("➕", key=f"add_{i}", help="在下方添加新反应"):
                st.session_state.reactions.insert(i+1, {
                    'equation': '',
                    'A': '',
                    'n': '',
                    'Ea': '',
                    'reference': ''
                })
                st.rerun()
        
        with col7:
            if len(st.session_state.reactions) > 1:
                if st.button("❌", key=f"del_{i}", help="删除此反应"):
                    st.session_state.reactions.pop(i)
                    st.rerun()

# 添加新反应按钮
if st.button("➕ 添加新反应", type="primary"):
    st.session_state.reactions.append({
        'equation': '',
        'A': '',
        'n': '',
        'Ea': '',
        'reference': ''
    })
    st.rerun()

# 计算和绘图
st.header("📊 反应速率常数对比")

# 准备有效的反应数据
valid_reactions = []
for i, reaction in enumerate(st.session_state.reactions):
    if reaction['equation'] and reaction['A'] and reaction['n'] and reaction['Ea']:
        A_val = parse_scientific_notation(reaction['A'])
        n_val = parse_scientific_notation(reaction['n'])
        Ea_val = parse_scientific_notation(reaction['Ea'])
        
        if A_val is not None and n_val is not None and Ea_val is not None:
            valid_reactions.append({
                'equation': reaction['equation'],
                'A': A_val,
                'n': n_val,
                'Ea': Ea_val,
                'reference': reaction['reference'],
                'index': i
            })

if valid_reactions:
    # 创建温度数组
    T = np.linspace(T_min, T_max, 500)
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # 存储所有log_k值用于自动范围计算
    all_log_k = []
    
    # 计算并绘制每个反应
    for i, reaction in enumerate(valid_reactions):
        k = calculate_rate_constant(T, reaction['A'], reaction['n'], reaction['Ea'], R_value)
        log_k = np.log10(k)
        all_log_k.extend(log_k)
        
        # 创建标签
        label = f"{reaction['equation']}"
        if reaction['reference']:
            label += f" ({reaction['reference']})"
        
        # 根据横轴类型选择x数据
        if x_axis_type == "1000/T (K⁻¹)":
            x_data = 1000.0 / T
        else:
            x_data = T
        
        # 绘制曲线
        color = generate_color(i)
        ax.plot(x_data, log_k, label=label, linewidth=line_width, color=color)
    
    # 设置图表格式
    if x_axis_type == "1000/T (K⁻¹)":
        ax.set_xlabel('1000/T (K⁻¹)', fontsize=12)
        # 设置x轴范围（注意1000/T时，大T对应小x值）
        ax.set_xlim(1000.0/T_max, 1000.0/T_min)
        
        # 添加第二个x轴显示温度值
        ax2 = ax.twiny()
        ax2.set_xlim(ax.get_xlim())
        
        # 选择一些温度值作为刻度
        temp_ticks = [300, 400, 500, 700, 1000, 1500, 2000, 2500, 3000]
        temp_ticks = [t for t in temp_ticks if T_min <= t <= T_max]
        inv_temp_ticks = [1000.0/t for t in temp_ticks]
        
        ax2.set_xticks(inv_temp_ticks)
        ax2.set_xticklabels([f'{t}K' for t in temp_ticks])
        ax2.set_xlabel('Temperature (K)', fontsize=10, color='gray')
        ax2.tick_params(axis='x', labelsize=8, colors='gray')
    else:
        ax.set_xlabel('Temperature (K)', fontsize=12)
        ax.set_xlim(T_min, T_max)
    
    ax.set_ylabel('log₁₀(k)', fontsize=12)
    
    # 根据横轴类型调整标题
    if x_axis_type == "1000/T (K⁻¹)":
        ax.set_title('Arrhenius Plot: Chemical Reaction Rate Constants', fontsize=14, fontweight='bold')
    else:
        ax.set_title('Chemical Reaction Rate Constants vs Temperature', fontsize=14, fontweight='bold')
    
    if show_grid:
        ax.grid(True, alpha=0.3, linestyle='--')
    
    if show_legend and len(valid_reactions) > 0:
        ax.legend(loc='best', framealpha=0.9)
    
    # 设置Y轴范围
    if y_axis_mode == "手动设置":
        ax.set_ylim(y_min, y_max)
    else:
        # 自动模式：基于数据范围稍微扩展
        if all_log_k:
            data_min = min(all_log_k)
            data_max = max(all_log_k)
            margin = (data_max - data_min) * 0.1  # 10%的边距
            ax.set_ylim(data_min - margin, data_max + margin)
    
    # 显示图表
    st.pyplot(fig)
    
    # 显示当前Y轴范围信息
    if y_axis_mode == "自动":
        current_ylim = ax.get_ylim()
        st.info(f"📏 当前Y轴范围：{current_ylim[0]:.2f} 到 {current_ylim[1]:.2f}")
    
    # 显示数据表格
    with st.expander("📋 查看详细数据"):
        # 创建数据表
        data_table = []
        for reaction in valid_reactions:
            k_300 = calculate_rate_constant(300, reaction['A'], reaction['n'], reaction['Ea'], R_value)
            k_1000 = calculate_rate_constant(1000, reaction['A'], reaction['n'], reaction['Ea'], R_value)
            k_2000 = calculate_rate_constant(2000, reaction['A'], reaction['n'], reaction['Ea'], R_value)
            
            data_table.append({
                '反应方程': reaction['equation'],
                'A (指前因子)': f"{reaction['A']:.2e}",
                'n (温度指数)': reaction['n'],
                'Ea (cal/mol)': f"{reaction['Ea']:.2e}", 
                '参考文献': reaction['reference'] or 'N/A',
                'k @ 300K': f"{k_300:.2e}",
                'log₁₀(k) @ 300K': f"{np.log10(k_300):.2f}",
                'k @ 1000K': f"{k_1000:.2e}",
                'log₁₀(k) @ 1000K': f"{np.log10(k_1000):.2f}",
                'k @ 2000K': f"{k_2000:.2e}",
                'log₁₀(k) @ 2000K': f"{np.log10(k_2000):.2f}"
            })
        
        df = pd.DataFrame(data_table)
        st.dataframe(df, use_container_width=True)
        
        # 下载CSV按钮
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 下载数据 (CSV)",
            data=csv,
            file_name="reaction_rates.csv",
            mime="text/csv"
        )
    
else:
    st.info("👆 请输入至少一个完整的反应参数（反应方程、A、n、Ea）来查看速率常数曲线")

# 添加使用示例
with st.expander("💡 使用示例"):
    st.markdown("""
    **示例输入：**
    
    | 反应方程 | A | n | Ea (cal/mol) | 参考文献 |
    |---------|---|---|------------|----------|
    | H + O2 = OH + O | 2.64e16 | -0.67 | 16800 | GRI-Mech 3.0 |
    | H2 + O = H + OH | 3.87e4 | 2.7 | 6260 | Smith 2020 |
    | NH3 + OH = NH2 + H2O | 5.0e7 | 1.6 | 955 | Miller 2019 |
    | H2NO + HO2 = HNO + H2O2 | 5.41e4 | 2.16 | -3597 | Stagni 2023 |
    | H2NO + O2 = HNO + HO2 | 1.73e5 | 2.19 | 18010 | Stagni 2023 |
    
    **科学计数法输入格式：**
    - 标准格式：`2.64e16` 或 `2.64E16`
    - 乘号格式：`2.64×10^16` 或 `2.64×1016`
    - 星号格式：`2.64*10^16`
    
    **横轴设置：**
    - **温度 T (K)**：直接显示温度，适合观察速率常数随温度的变化趋势
    - **1000/T (K⁻¹)**：Arrhenius图，可以从直线斜率计算活化能，适合动力学分析
    
    **Y轴范围调节：**
    - 在左侧边栏中可以选择"自动"或"手动设置"Y轴范围
    - 自动模式会根据数据自动调整最佳显示范围
    - 手动模式可以精确控制Y轴的显示范围
    """)

# 添加公式说明
with st.expander("📚 公式说明"):
    st.markdown("""
    **Arrhenius方程：**
    
    $$k = AT^n \\exp\\left(-\\frac{E_a}{RT}\\right)$$
    
    其中：
    - k: 反应速率常数
    - A: 指前因子（频率因子）
    - T: 绝对温度 (K)
    - n: 温度指数
    - Ea: 活化能 (cal/mol)
    - R: 理想气体常数 (1.987 cal/(mol·K))
    
    **对数形式：**
    
    $$\\log_{10}(k) = \\log_{10}(A) + n\\log_{10}(T) - \\frac{E_a}{2.303RT}$$
    
    **Arrhenius图（1000/T为横轴）：**
    
    当 n = 0 时，以 1000/T 为横轴，log₁₀(k) 为纵轴，可得到直线：
    
    $$\\log_{10}(k) = \\log_{10}(A) - \\frac{E_a}{2.303R} \\cdot \\frac{1000}{T} \\cdot \\frac{1}{1000}$$
    
    从直线斜率可以计算活化能：
    $$E_a = -2.303R \\times 1000 \\times \\text{斜率}$$
    """)
