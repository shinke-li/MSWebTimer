import streamlit as st
import time
from datetime import datetime
import base64

def get_audio_html(sound_type):
    return f'''
        <audio id="audioPlayer" style="display:none;">
            <source src="data:audio/wav;base64,{sound_type}" type="audio/wav">
        </audio>
        <script>
            var audio = document.getElementById('audioPlayer');
            audio.volume = 1;
            audio.play();
        </script>
    '''

def get_init_audio_html():
    # 初始化音频系统的HTML，包含一个简短的无声音频
    return '''
        <div id="initAudioDiv">
            <button onclick="initAudio()" style="padding: 10px; background-color: #ff4b4b; color: white; border: none; border-radius: 5px;">
                点击初始化音频系统
            </button>
            <audio id="initAudio" style="display:none;">
                <source src="data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA" type="audio/wav">
            </audio>
            <script>
                function initAudio() {
                    var audio = document.getElementById('initAudio');
                    audio.play().then(() => {
                        document.getElementById('initAudioDiv').style.display = 'none';
                        window.parent.postMessage({type: 'audioInitialized'}, '*');
                    }).catch(e => {
                        console.error('Audio init failed:', e);
                    });
                }
            </script>
        </div>
    '''

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

    # 显示音频初始化按钮
    if not st.session_state.audio_initialized:
        st.markdown(get_init_audio_html(), unsafe_allow_html=True)
        
        # 添加JavaScript监听器来接收初始化完成的消息
        st.markdown('''
            <script>
                window.addEventListener('message', function(e) {
                    if (e.data.type === 'audioInitialized') {
                        // 通过修改URL参数来触发页面刷新
                        var url = new URL(window.location.href);
                        url.searchParams.set('audio_init', 'true');
                        window.location.href = url.toString();
                    }
                });
            </script>
        ''', unsafe_allow_html=True)

        # 检查URL参数来更新初始化状态
        if st.query_params.get('audio_init') == 'true':
            st.session_state.audio_initialized = True
            st.query_params.clear()  # 清除URL参数
            st.rerun()

    # 音频播放器容器
    audio_placeholder = st.empty()
    
    # 仅在音频已初始化时显示和处理声音
    if st.session_state.audio_initialized and st.session_state.play_sound:
        if st.session_state.sound_type == 'phase1':
            audio_placeholder.markdown(get_audio_html(st.session_state.audio_bytes1), unsafe_allow_html=True)
        elif st.session_state.sound_type == 'phase2':
            audio_placeholder.markdown(get_audio_html(st.session_state.audio_bytes2), unsafe_allow_html=True)
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
        
        # 只有在音频初始化后才启用按钮
        if st.session_state.audio_initialized:
            if st.session_state.phase == "待开始":
                if st.button("开始", key="start_button", use_container_width=True):
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

    # 计时器逻辑保持不变
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
