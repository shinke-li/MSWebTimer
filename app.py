import streamlit as st
import time
from datetime import datetime
import base64

def get_ios_audio_js():
    return """
    <script>
    class IOSAudioPlayer {
        constructor() {
            this.audioElements = {};
            this.initialized = false;
        }

        async init() {
            // 创建隐藏的音频元素
            const createAudio = (key, base64Data) => {
                const audio = document.createElement('audio');
                audio.style.display = 'none';
                audio.preload = 'auto';
                // 设置为较短的音频片段以确保快速加载
                audio.src = `data:audio/wav;base64,${base64Data}`;
                // iOS需要这些属性
                audio.setAttribute('playsinline', '');
                audio.setAttribute('webkit-playsinline', '');
                document.body.appendChild(audio);
                this.audioElements[key] = audio;
                
                // 监听加载完成事件
                audio.addEventListener('canplaythrough', () => {
                    console.log(`Audio ${key} loaded`);
                });
                
                // 错误处理
                audio.addEventListener('error', (e) => {
                    console.error(`Error loading audio ${key}:`, e);
                });
            };

            try {
                this.initialized = true;
                console.log('Audio system initialized');
                return true;
            } catch (e) {
                console.error('Failed to initialize audio:', e);
                return false;
            }
        }

        loadSound(key, base64Data) {
            if (!this.initialized) {
                console.error('Audio system not initialized');
                return;
            }
            
            try {
                // 如果已存在，先移除旧的
                if (this.audioElements[key]) {
                    this.audioElements[key].remove();
                }
                
                const audio = document.createElement('audio');
                audio.style.display = 'none';
                audio.preload = 'auto';
                audio.src = `data:audio/wav;base64,${base64Data}`;
                audio.setAttribute('playsinline', '');
                audio.setAttribute('webkit-playsinline', '');
                document.body.appendChild(audio);
                this.audioElements[key] = audio;
                
                console.log(`Sound ${key} loaded`);
            } catch (e) {
                console.error(`Failed to load sound ${key}:`, e);
            }
        }

        async play(key) {
            const audio = this.audioElements[key];
            if (!audio) {
                console.error(`Sound ${key} not found`);
                return;
            }

            try {
                // 重置音频到开始位置
                audio.currentTime = 0;
                
                // 尝试播放
                const playPromise = audio.play();
                if (playPromise !== undefined) {
                    playPromise.catch(error => {
                        console.error(`Playback failed:`, error);
                        // 如果自动播放失败，我们创建一个按钮让用户手动触发
                        if (!document.getElementById('manual-play-button')) {
                            const button = document.createElement('button');
                            button.id = 'manual-play-button';
                            button.innerHTML = '点击播放声音';
                            button.style.display = 'none';
                            button.onclick = () => {
                                audio.play();
                                button.remove();
                            };
                            document.body.appendChild(button);
                            button.click();  // 自动点击按钮
                        }
                    });
                }
            } catch (e) {
                console.error(`Failed to play sound ${key}:`, e);
            }
        }
    }

    // 创建全局实例
    window.iosAudioPlayer = new IOSAudioPlayer();
    </script>
    """

def main():
    st.set_page_config(layout="wide")

    # 注入iOS音频系统
    st.markdown(get_ios_audio_js(), unsafe_allow_html=True)

    # 初始化音频系统并加载音频
    if 'audio_initialized' not in st.session_state:
        st.session_state.audio_initialized = False

    # 加载音频文件
    if not st.session_state.audio_initialized:
        with open('phase1.wav', 'rb') as f:
            audio_data1 = base64.b64encode(f.read()).decode()
        with open('phase2.wav', 'rb') as f:
            audio_data2 = base64.b64encode(f.read()).decode()
        
        # 初始化音频系统
        st.markdown("""
            <script>
            if (window.iosAudioPlayer) {
                window.iosAudioPlayer.init();
                window.iosAudioPlayer.loadSound('phase1', '%s');
                window.iosAudioPlayer.loadSound('phase2', '%s');
            }
            </script>
        """ % (audio_data1, audio_data2), unsafe_allow_html=True)
        
        st.session_state.audio_initialized = True

    st.markdown("<h1 style='text-align: center;'>气体检测计时器</h1>", unsafe_allow_html=True)

    # 初始化其他状态
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

    def play_sound(sound_key):
        st.markdown(f"""
            <script>
            if (window.iosAudioPlayer) {{
                window.iosAudioPlayer.play('{sound_key}');
            }}
            </script>
        """, unsafe_allow_html=True)
    
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
        
        if st.session_state.phase == "待开始":
            if st.button("开始", key="start_button", use_container_width=True):
                st.session_state.phase = "气袋检测中"
                st.session_state.timer_running = True
                st.rerun()
        elif st.session_state.phase == "等待清洗":
            play_sound('phase1')
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
            
            play_sound('phase2')
            
            # 重置状态
            st.session_state.timer_running = False
            st.session_state.current_state = "就绪"
            st.session_state.phase = "待开始"
            st.session_state.sample_progress_value = 0
            st.session_state.zero_progress_value = 0
            st.rerun()

if __name__ == "__main__":
    main()
