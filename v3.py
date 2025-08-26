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

# 定义线型和标记样式选项
LINE_STYLES = {
    '实线': '-',
    '虚线': '--',
    '点线': ':',
    '点划线': '-.',
}

MARKER_STYLES = {
    '无': '',
    '圆形': 'o',
    '方形': 's',
    '三角形(上)': '^',
    '三角形(下)': 'v',
    '菱形': 'D',
    '五边形': 'p',
    '六边形': 'h',
    '加号': '+',
    '叉号': 'x',
    '星形': '*',
}

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
    # 使用更多样的颜色
    colors_list = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                   '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    return colors_list[index % len(colors_list)]

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
    
    # Duplicate反应显示选项
    st.subheader("Duplicate反应显示")
    show_duplicate_components = st.checkbox(
        "显示duplicate反应的各分量",
        value=False,
        help="勾选后会用虚线显示duplicate反应的各个分量"
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
    marker_size = st.slider("标记大小", min_value=0, max_value=15, value=6)
    marker_frequency = st.slider(
        "标记密度", 
        min_value=1, 
        max_value=50, 
        value=10,
        help="每隔多少个数据点显示一个标记"
    )

# 初始化session state
if 'reactions' not in st.session_state:
    st.session_state.reactions = []

# 主界面 - 输入区域
st.header("📝 输入反应参数")

st.markdown("""
**输入说明:**
- 点击"添加单一速率反应"添加普通反应（一组A、n、Ea参数）
- 点击"添加Duplicate反应"添加具有多个速率通道的反应（多组A、n、Ea参数）
- 可以为每个反应自定义线型和标记样式
""")

# 添加反应按钮
col1, col2 = st.columns(2)
with col1:
    if st.button("➕ 添加单一速率反应", type="primary", use_container_width=True):
        st.session_state.reactions.append({
            'type': 'single',
            'equation': '',
            'reference': '',
            'parameters': [{'A': '', 'n': '', 'Ea': ''}],
            'line_style': '实线',
            'marker_style': '无',
            'custom_color': None
        })
        st.rerun()

with col2:
    if st.button("➕ 添加Duplicate反应", type="secondary", use_container_width=True):
        st.session_state.reactions.append({
            'type': 'duplicate',
            'equation': '',
            'reference': '',
            'parameters': [{'A': '', 'n': '', 'Ea': ''}, {'A': '', 'n': '', 'Ea': ''}],
            'line_style': '实线',
            'marker_style': '无',
            'custom_color': None
        })
        st.rerun()

# 显示所有反应
for i, reaction in enumerate(st.session_state.reactions):
    with st.expander(f"**反应 {i+1}** - {reaction.get('equation', '未命名')} ({'Duplicate' if reaction['type'] == 'duplicate' else '单一速率'})", expanded=True):
        # 反应方程和参考文献
        col1, col2 = st.columns([3, 2])
        with col1:
            reaction['equation'] = st.text_input(
                "反应方程",
                value=reaction['equation'],
                key=f"eq_{i}",
                placeholder="如: H + O2 = OH + O"
            )
        with col2:
            reaction['reference'] = st.text_input(
                "参考文献",
                value=reaction['reference'],
                key=f"ref_{i}",
                placeholder="Smith 2020"
            )
        
        # 显示样式设置
        st.markdown("**显示样式：**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            reaction['line_style'] = st.selectbox(
                "线型",
                options=list(LINE_STYLES.keys()),
                index=list(LINE_STYLES.keys()).index(reaction.get('line_style', '实线')),
                key=f"line_style_{i}"
            )
        with col2:
            reaction['marker_style'] = st.selectbox(
                "标记",
                options=list(MARKER_STYLES.keys()),
                index=list(MARKER_STYLES.keys()).index(reaction.get('marker_style', '无')),
                key=f"marker_style_{i}"
            )
        with col3:
            # 颜色选择
            use_custom_color = st.checkbox("自定义颜色", key=f"use_color_{i}")
            if use_custom_color:
                reaction['custom_color'] = st.color_picker(
                    "选择颜色",
                    value=reaction.get('custom_color', generate_color(i)),
                    key=f"color_{i}"
                )
            else:
                reaction['custom_color'] = None
        with col4:
            if st.button("🗑️ 删除反应", key=f"del_reaction_{i}"):
                st.session_state.reactions.pop(i)
                st.rerun()
        
        # 速率参数
        st.markdown("**速率参数：**")
        if reaction['type'] == 'single':
            # 单一速率反应
            col1, col2, col3 = st.columns(3)
            with col1:
                reaction['parameters'][0]['A'] = st.text_input(
                    "A (指前因子)",
                    value=reaction['parameters'][0]['A'],
                    key=f"A_{i}_0",
                    placeholder="1.5e13"
                )
            with col2:
                reaction['parameters'][0]['n'] = st.text_input(
                    "n (温度指数)",
                    value=reaction['parameters'][0]['n'],
                    key=f"n_{i}_0",
                    placeholder="0"
                )
            with col3:
                reaction['parameters'][0]['Ea'] = st.text_input(
                    "Ea (cal/mol)",
                    value=reaction['parameters'][0]['Ea'],
                    key=f"Ea_{i}_0",
                    placeholder="50000"
                )
        else:
            # Duplicate反应
            for j, params in enumerate(reaction['parameters']):
                col0, col1, col2, col3, col4 = st.columns([1, 3, 2.5, 2.5, 1])
                with col0:
                    st.write(f"通道 {j+1}")
                with col1:
                    params['A'] = st.text_input(
                        f"A",
                        value=params['A'],
                        key=f"A_{i}_{j}",
                        placeholder="1.5e13",
                        label_visibility="collapsed"
                    )
                with col2:
                    params['n'] = st.text_input(
                        f"n",
                        value=params['n'],
                        key=f"n_{i}_{j}",
                        placeholder="0",
                        label_visibility="collapsed"
                    )
                with col3:
                    params['Ea'] = st.text_input(
                        f"Ea",
                        value=params['Ea'],
                        key=f"Ea_{i}_{j}",
                        placeholder="50000",
                        label_visibility="collapsed"
                    )
                with col4:
                    if len(reaction['parameters']) > 1:
                        if st.button("❌", key=f"del_param_{i}_{j}"):
                            reaction['parameters'].pop(j)
                            st.rerun()
            
            # 添加通道按钮
            if st.button("➕ 添加通道", key=f"add_channel_{i}"):
                reaction['parameters'].append({'A': '', 'n': '', 'Ea': ''})
                st.rerun()

# 计算和绘图
st.header("📊 反应速率常数对比")

# 准备有效的反应数据
valid_reactions = []
for reaction in st.session_state.reactions:
    if reaction['equation']:
        # 检查参数完整性
        valid_params = []
        for params in reaction['parameters']:
            if params['A'] and params['n'] and params['Ea']:
                A_val = parse_scientific_notation(params['A'])
                n_val = parse_scientific_notation(params['n'])
                Ea_val = parse_scientific_notation(params['Ea'])
                
                if A_val is not None and n_val is not None and Ea_val is not None:
                    valid_params.append({
                        'A': A_val,
                        'n': n_val,
                        'Ea': Ea_val
                    })
        
        if valid_params:
            valid_reactions.append({
                'type': reaction['type'],
                'equation': reaction['equation'],
                'reference': reaction['reference'],
                'parameters': valid_params,
                'line_style': reaction.get('line_style', '实线'),
                'marker_style': reaction.get('marker_style', '无'),
                'custom_color': reaction.get('custom_color', None)
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
        # 确定颜色
        if reaction['custom_color']:
            color = reaction['custom_color']
        else:
            color = generate_color(i)
        
        # 获取线型和标记
        line_style = LINE_STYLES[reaction['line_style']]
        marker_style = MARKER_STYLES[reaction['marker_style']]
        
        if reaction['type'] == 'single':
            # 单一速率反应
            params = reaction['parameters'][0]
            k = calculate_rate_constant(T, params['A'], params['n'], params['Ea'], R_value)
            log_k = np.log10(k)
            all_log_k.extend(log_k)
            
            # 创建标签
            label = f"{reaction['equation']}"
            if reaction['reference']:
                label += f" [{reaction['reference']}]"
            
            # 根据横轴类型选择x数据
            if x_axis_type == "1000/T (K⁻¹)":
                x_data = 1000.0 / T
            else:
                x_data = T
            
            # 绘制曲线
            if marker_style:
                # 带标记的曲线
                ax.plot(x_data[::marker_frequency], log_k[::marker_frequency], 
                       marker=marker_style, markersize=marker_size,
                       linestyle='', color=color, label='_nolegend_')
                ax.plot(x_data, log_k, label=label, linewidth=line_width, 
                       color=color, linestyle=line_style)
            else:
                # 只有线条
                ax.plot(x_data, log_k, label=label, linewidth=line_width, 
                       color=color, linestyle=line_style)
            
        else:
            # Duplicate反应
            # 计算各分量速率常数
            k_components = []
            for params in reaction['parameters']:
                k = calculate_rate_constant(T, params['A'], params['n'], params['Ea'], R_value)
                k_components.append(k)
            
            # 计算总速率常数
            k_total = np.sum(k_components, axis=0)
            log_k_total = np.log10(k_total)
            all_log_k.extend(log_k_total)
            
            # 创建标签
            label = f"{reaction['equation']} (sum of {len(reaction['parameters'])} channels)"
            if reaction['reference']:
                label += f" [{reaction['reference']}]"
            
            # 根据横轴类型选择x数据
            if x_axis_type == "1000/T (K⁻¹)":
                x_data = 1000.0 / T
            else:
                x_data = T
            
            # 绘制总速率常数
            if marker_style:
                # 带标记的曲线
                ax.plot(x_data[::marker_frequency], log_k_total[::marker_frequency], 
                       marker=marker_style, markersize=marker_size,
                       linestyle='', color=color, label='_nolegend_')
                ax.plot(x_data, log_k_total, label=label, linewidth=line_width, 
                       color=color, linestyle=line_style)
            else:
                # 只有线条
                ax.plot(x_data, log_k_total, label=label, linewidth=line_width, 
                       color=color, linestyle=line_style)
            
            # 如果选择显示分量，绘制各个分量
            if show_duplicate_components:
                for j, k_comp in enumerate(k_components):
                    log_k_comp = np.log10(k_comp)
                    all_log_k.extend(log_k_comp)
                    
                    comp_label = f"  └─ Channel {j+1}"
                    ax.plot(x_data, log_k_comp, label=comp_label, 
                           linewidth=line_width*0.6, color=color, 
                           linestyle=':', alpha=0.5)
    
    # 设置图表格式
    if x_axis_type == "1000/T (K⁻¹)":
        ax.set_xlabel('1000/T (K⁻¹)', fontsize=12)
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
    
    if show_legend:
        ax.legend(loc='best', framealpha=0.9, fontsize=8)
    
    # 设置Y轴范围
    if y_axis_mode == "手动设置":
        ax.set_ylim(y_min, y_max)
    else:
        # 自动模式：基于数据范围稍微扩展
        if all_log_k:
            data_min = min(all_log_k)
            data_max = max(all_log_k)
            margin = (data_max - data_min) * 0.1
            ax.set_ylim(data_min - margin, data_max + margin)
    
    # 显示图表
    st.pyplot(fig)
    
    # 显示数据表格
    with st.expander("📋 查看详细数据"):
        # 创建数据表
        data_table = []
        for reaction in valid_reactions:
            if reaction['type'] == 'single':
                # 单一速率反应
                params = reaction['parameters'][0]
                k_300 = calculate_rate_constant(300, params['A'], params['n'], params['Ea'], R_value)
                k_1000 = calculate_rate_constant(1000, params['A'], params['n'], params['Ea'], R_value)
                k_2000 = calculate_rate_constant(2000, params['A'], params['n'], params['Ea'], R_value)
                
                data_table.append({
                    '反应方程': reaction['equation'],
                    '类型': '单一速率',
                    'A': f"{params['A']:.2e}",
                    'n': f"{params['n']:.3f}",
                    'Ea (cal/mol)': f"{params['Ea']:.0f}",
                    '参考文献': reaction['reference'] or 'N/A',
                    '线型': reaction['line_style'],
                    '标记': reaction['marker_style'],
                    'k @ 300K': f"{k_300:.2e}",
                    'k @ 1000K': f"{k_1000:.2e}",
                    'k @ 2000K': f"{k_2000:.2e}"
                })
            else:
                # Duplicate反应 - 各分量
                for j, params in enumerate(reaction['parameters']):
                    k_300 = calculate_rate_constant(300, params['A'], params['n'], params['Ea'], R_value)
                    k_1000 = calculate_rate_constant(1000, params['A'], params['n'], params['Ea'], R_value)
                    k_2000 = calculate_rate_constant(2000, params['A'], params['n'], params['Ea'], R_value)
                    
                    data_table.append({
                        '反应方程': reaction['equation'],
                        '类型': f'Duplicate-通道{j+1}',
                        'A': f"{params['A']:.2e}",
                        'n': f"{params['n']:.3f}",
                        'Ea (cal/mol)': f"{params['Ea']:.0f}",
                        '参考文献': reaction['reference'] or 'N/A',
                        '线型': '-',
                        '标记': '-',
                        'k @ 300K': f"{k_300:.2e}",
                        'k @ 1000K': f"{k_1000:.2e}",
                        'k @ 2000K': f"{k_2000:.2e}"
                    })
                
                # 总和
                k_total_300 = sum([calculate_rate_constant(300, p['A'], p['n'], p['Ea'], R_value) 
                                 for p in reaction['parameters']])
                k_total_1000 = sum([calculate_rate_constant(1000, p['A'], p['n'], p['Ea'], R_value) 
                                   for p in reaction['parameters']])
                k_total_2000 = sum([calculate_rate_constant(2000, p['A'], p['n'], p['Ea'], R_value) 
                                   for p in reaction['parameters']])
                
                data_table.append({
                    '反应方程': reaction['equation'],
                    '类型': 'Duplicate-总和',
                    'A': '-',
                    'n': '-',
                    'Ea (cal/mol)': '-',
                    '参考文献': reaction['reference'] or 'N/A',
                    '线型': reaction['line_style'],
                    '标记': reaction['marker_style'],
                    'k @ 300K': f"{k_total_300:.2e}",
                    'k @ 1000K': f"{k_total_1000:.2e}",
                    'k @ 2000K': f"{k_total_2000:.2e}"
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
    st.info("👆 请添加反应并输入完整参数来查看速率常数曲线")

# 添加使用示例
with st.expander("💡 使用示例"):
    st.markdown("""
    **使用场景示例：**
    
    对比多个文献中同一反应的速率常数时，可以使用不同的线型和标记来区分：
    
    1. **文献A (单一速率)**：
       - 反应：H2NO + HO2 = HNO + H2O2
       - 线型：实线，标记：圆形
       - 参考文献：Smith 2020
    
    2. **文献B (Duplicate反应)**：
       - 反应：H2NO + HO2 = HNO + H2O2  
       - 线型：虚线，标记：三角形
       - 参考文献：Stagni 2023
    
    3. **文献C (单一速率)**：
       - 反应：H2NO + HO2 = HNO + H2O2
       - 线型：点划线，标记：方形
       - 参考文献：Miller 2019
    
    **样式设置技巧：**
    - 使用不同线型区分不同来源（实线、虚线、点线、点划线）
    - 使用标记符号强调重要数据点
    - 自定义颜色用于特定分组
    - 调整标记密度避免图表过于拥挤
    
    **科学计数法输入格式：**
    - 标准格式：`2.64e16` 或 `2.64E16`
    - 乘号格式：`2.64×10^16` 或 `2.64×1016`
    - 星号格式：`2.64*10^16`
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
    
    **Duplicate反应：**
    
    当同一个反应有多个速率通道时：
    $$k_{total} = k_1 + k_2 + ... + k_n$$
    
    每个通道有独立的Arrhenius参数：
    $$k_i = A_i T^{n_i} \\exp\\left(-\\frac{E_{a,i}}{RT}\\right)$$
    """)
