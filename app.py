import streamlit as st
import time
from datetime import datetime
import base64

def get_audio_html(sound_type):
    # 使用JavaScript来触发音频播放
    audio_html = f"""
        <div id="audio-container">
            <audio id="audio-player" preload="auto">
                <source src="data:audio/wav;base64,{sound_type}" type="audio/wav">
            </audio>
        </div>
        <script>
            const audioPlayer = document.getElementById('audio-player');
            // 尝试播放
            const playAttempt = audioPlayer.play();
            
            if (playAttempt !== undefined) {{
                playAttempt.catch(e => {{
                    // 如果自动播放失败，我们设置一个很短的超时后再次尝试
                    setTimeout(() => {{
                        audioPlayer.play().catch(err => console.log('Second play attempt failed'));
                    }}, 100);
                }});
            }}
        </script>
    """
    return audio_html

def main():
    st.set_page_config(layout="wide")
    
    # 加载音频文件
    if 'audio_bytes1' not in st.session_state:
        with open('phase1.wav', 'rb') as f:
            st.session_state.audio_bytes1 = base64.b64encode(f.read()).decode()
    if 'audio_bytes2' not in st.session_state:
        with open('phase2.wav', 'rb') as f:
            st.session_state.audio_bytes2 = base64.b64encode(f.read()).decode()
    
    # 初始化会话状态
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
    if 'user_interacted' not in st.session_state:
        st.session_state.user_interacted = False

    st.markdown("<h1 style='text-align: center;'>气体检测计时器</h1>", unsafe_allow_html=True)
    
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
    
    # 音频播放器容器
    audio_placeholder = st.empty()
    
    # 播放声音的逻辑
    if st.session_state.play_sound and st.session_state.user_interacted:
        if st.session_state.sound_type == 'phase1':
            audio_placeholder.markdown(get_audio_html(st.session_state.audio_bytes1), unsafe_allow_html=True)
        elif st.session_state.sound_type == 'phase2':
            audio_placeholder.markdown(get_audio_html(st.session_state.audio_bytes2), unsafe_allow_html=True)
        st.session_state.play_sound = False
        st.session_state.sound_type = None
    
    # 按钮布局
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
        
        if st.session_state.phase == "待开始":
            if st.button("开始", key="start_button", use_container_width=True):
                st.session_state.user_interacted = True  # 标记用户已交互
                st.session_state.phase = "气袋检测中"
                st.session_state.timer_running = True
                st.rerun()
        elif st.session_state.phase == "等待清洗":
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
            
            st.session_state.play_sound = True
            st.session_state.sound_type = 'phase2'
            
            # 重置状态
            st.session_state.timer_running = False
            st.session_state.current_state = "就绪"
            st.session_state.phase = "待开始"
            st.session_state.sample_progress_value = 0
            st.session_state.zero_progress_value = 0
            st.rerun()

if __name__ == "__main__":
    main()
