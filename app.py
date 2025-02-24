import streamlit as st
import time
from datetime import datetime
import base64

def main():
    st.set_page_config(layout="wide")

    # 加载音频文件
    if 'audio_bytes1' not in st.session_state:
        with open('phase1.wav', 'rb') as f:
            st.session_state.audio_bytes1 = f.read()  # 不需要base64编码
    if 'audio_bytes2' not in st.session_state:
        with open('phase2.wav', 'rb') as f:
            st.session_state.audio_bytes2 = f.read()  # 不需要base64编码
    
    # 初始化会话状态
    if 'audio_initialized' not in st.session_state:
        st.session_state.audio_initialized = False
    if 'timer_running' not in st.session_state:
        st.session_state.timer_running = False
    if 'current_state' not in st.session_state:
        st.session_state.current_state = "就绪"
    if 'phase' not in st.session_state:
        st.session_state.phase = "待开始"
    if 'sample_progress_value' not in st.session_state:
        st.session_state.sample_progress_value = 0
    if 'zero_progress_value' not in st.session_state:
        st.session_state.zero_progress_value = 0
    if 'play_sound' not in st.session_state:
        st.session_state.play_sound = False
    if 'sound_type' not in st.session_state:
        st.session_state.sound_type = None

    st.markdown("<h1 style='text-align: center;'>气体检测计时器</h1>", unsafe_allow_html=True)

    # 初始化音频系统
    if not st.session_state.audio_initialized:
        st.markdown("<h3 style='text-align: center; color: #ff4b4b;'>请先初始化音频系统</h3>", unsafe_allow_html=True)
        init_col1, init_col2, init_col3 = st.columns([2, 1, 2])
        with init_col2:
            if st.button("初始化音频系统", key="init_audio", use_container_width=True, type="primary"):
                st.session_state.audio_initialized = True
                st.audio(st.session_state.audio_bytes1, format='audio/wav')
                st.rerun()
    
    # 音频播放器容器
    audio_player = st.empty()
    
    # 根据状态播放声音
    if st.session_state.play_sound and st.session_state.audio_initialized:
        if st.session_state.sound_type == 'phase1':
            audio_player.audio(st.session_state.audio_bytes1, format='audio/wav')
        elif st.session_state.sound_type == 'phase2':
            audio_player.audio(st.session_state.audio_bytes2, format='audio/wav')
        st.session_state.play_sound = False
        st.session_state.sound_type = None

    # 输入参数
    col1, col2 = st.columns(2)
    with col1:
        zero_gas_time = st.number_input("零气时间(秒)", value=50, min_value=1)
        zero_gas_count = st.number_input("零气计数", value=2, min_value=1)
    with col2:
        sample_gas_time = st.number_input("气袋时间(秒)", value=50, min_value=1)
        sample_gas_count = st.number_input("气袋计数", value=3, min_value=1)

    # 状态显示
    st.markdown(f"<h2 style='text-align: center;'>状态: {st.session_state.current_state}</h2>", unsafe_allow_html=True)
    
    # 进度条
    with st.container():
        st.markdown("### 气袋检测进度")
        sample_progress = st.progress(st.session_state.sample_progress_value)
        st.markdown("### 零气清洗进度")
        zero_progress = st.progress(st.session_state.zero_progress_value)
    
    # 时间显示
    time_display = st.empty()
    
    # 控制按钮
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        button_style = """
        <style>
        div.stButton > button {
            font-size: 24px;
            height: 60px;
        }
        </style>
        """
        st.markdown(button_style, unsafe_allow_html=True)
        
        if st.session_state.audio_initialized:
            if st.session_state.phase == "待开始":
                if st.button("开始", key="start_button", use_container_width=True):
                    st.session_state.phase = "气袋检测中"
                    st.session_state.timer_running = True
                    st.rerun()
            elif st.session_state.phase == "等待清洗":
                # 直接在这里播放第一阶段完成的声音
                audio_player.audio(st.session_state.audio_bytes1, format='audio/wav')
                if st.button("清洗", key="wash_button", use_container_width=True):
                    st.session_state.phase = "清洗中"
                    st.session_state.timer_running = True
                    st.rerun()
            else:
                st.button("进行中...", disabled=True, key="disabled_button", use_container_width=True)

    # 计时器逻辑
    if st.session_state.timer_running:
        if st.session_state.phase == "气袋检测中":
            total_sample_time = sample_gas_time * sample_gas_count
            st.session_state.current_state = "气袋检测"
            start_time = time.time()
            
            while (time.time() - start_time) < total_sample_time:
                elapsed = time.time() - start_time
                progress = elapsed / total_sample_time
                st.session_state.sample_progress_value = progress
                sample_progress.progress(progress)
                time_display.markdown(f"<div style='text-align: center; font-size: 24px;'>剩余时间: {int(total_sample_time - elapsed)}秒</div>", unsafe_allow_html=True)
                time.sleep(0.1)
            
            st.session_state.play_sound = True
            st.session_state.sound_type = 'phase1'
            st.session_state.phase = "等待清洗"
            st.session_state.timer_running = False
            st.rerun()
            
        elif st.session_state.phase == "清洗中":
            total_zero_time = zero_gas_time * zero_gas_count
            st.session_state.current_state = "零气清洗"
            start_time = time.time()
            
            while (time.time() - start_time) < total_zero_time:
                elapsed = time.time() - start_time
                progress = elapsed / total_zero_time
                st.session_state.zero_progress_value = progress
                zero_progress.progress(progress)
                time_display.markdown(f"<div style='text-align: center; font-size: 24px;'>剩余时间: {int(total_zero_time - elapsed)}秒</div>", unsafe_allow_html=True)
                time.sleep(0.1)
            
            # 直接播放第二阶段完成的声音
            audio_player.audio(st.session_state.audio_bytes2, format='audio/wav')
            
            # 重置状态
            st.session_state.timer_running = False
            st.session_state.current_state = "就绪"
            st.session_state.phase = "待开始"
            st.session_state.sample_progress_value = 0
            st.session_state.zero_progress_value = 0
            st.rerun()

if __name__ == "__main__":
    main()
