import streamlit as st
import time
from datetime import datetime
import base64

def get_audio_system_js():
    return """
    <script>
    class AudioSystem {
        constructor() {
            this.audioContext = null;
            this.audioBuffers = {};
            this.isInitialized = false;
        }

        async initialize() {
            if (this.isInitialized) return;
            
            try {
                // 创建音频上下文
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                
                // 创建一个短暂的音频缓冲区（用于初始化）
                const buffer = this.audioContext.createBuffer(1, 1, 22050);
                const source = this.audioContext.createBufferSource();
                source.buffer = buffer;
                source.connect(this.audioContext.destination);
                source.start(0);
                
                this.isInitialized = true;
                
                // 发送初始化成功消息
                window.parent.postMessage({type: 'audioInitialized'}, '*');
            } catch (error) {
                console.error('Failed to initialize audio system:', error);
            }
        }

        async loadSound(key, base64Data) {
            if (!this.isInitialized) return;
            
            try {
                // 解码base64数据
                const binaryString = window.atob(base64Data);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                
                // 解码音频数据
                const audioBuffer = await this.audioContext.decodeAudioData(bytes.buffer);
                this.audioBuffers[key] = audioBuffer;
            } catch (error) {
                console.error('Failed to load sound:', error);
            }
        }

        async playSound(key) {
            if (!this.isInitialized || !this.audioBuffers[key]) return;
            
            try {
                // 恢复音频上下文（如果被暂停）
                if (this.audioContext.state === 'suspended') {
                    await this.audioContext.resume();
                }
                
                // 创建音源并播放
                const source = this.audioContext.createBufferSource();
                source.buffer = this.audioBuffers[key];
                source.connect(this.audioContext.destination);
                source.start(0);
                
                // 通知播放成功
                window.parent.postMessage({type: 'audioPlayed', key: key}, '*');
            } catch (error) {
                console.error('Failed to play sound:', error);
            }
        }
    }

    // 创建全局音频系统实例
    if (!window.audioSystem) {
        window.audioSystem = new AudioSystem();
    }
    
    // 监听来自Streamlit的消息
    window.addEventListener('message', async function(event) {
        const audioSystem = window.audioSystem;
        
        if (event.data.type === 'initializeAudio') {
            await audioSystem.initialize();
        } else if (event.data.type === 'loadSound') {
            await audioSystem.loadSound(event.data.key, event.data.data);
        } else if (event.data.type === 'playSound') {
            await audioSystem.playSound(event.data.key);
        }
    });
    </script>
    """

def initialize_audio_system():
    # 注入音频系统JavaScript
    st.markdown(get_audio_system_js(), unsafe_allow_html=True)
    
    # 添加消息监听器
    st.markdown("""
        <script>
        window.addEventListener('message', function(e) {
            if (e.data.type === 'audioInitialized') {
                // 通过修改URL参数来触发页面刷新
                const url = new URL(window.location.href);
                url.searchParams.set('audio_init', 'true');
                window.location.href = url.toString();
            }
        });
        </script>
    """, unsafe_allow_html=True)

def load_audio_file(file_path):
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def send_audio_command(command_type, **kwargs):
    # 构建JavaScript命令
    command = f"""
        <script>
        if (window.audioSystem) {{
            window.audioSystem.{command_type}({kwargs.get('args', '')});
        }}
        </script>
    """
    st.markdown(command, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide")

    # 初始化音频系统
    if 'audio_initialized' not in st.session_state:
        st.session_state.audio_initialized = False
        initialize_audio_system()

    # 加载音频文件
    if 'audio_loaded' not in st.session_state:
        st.session_state.audio_loaded = False
        st.session_state.audio_bytes1 = load_audio_file('phase1.wav')
        st.session_state.audio_bytes2 = load_audio_file('phase2.wav')
    
    # 检查URL参数来更新初始化状态
    if st.query_params.get('audio_init') == 'true':
        st.session_state.audio_initialized = True
        if not st.session_state.audio_loaded:
            # 加载音频文件
            st.markdown(f"""
                <script>
                if (window.audioSystem) {{
                    window.audioSystem.loadSound('phase1', '{st.session_state.audio_bytes1}');
                    window.audioSystem.loadSound('phase2', '{st.session_state.audio_bytes2}');
                }}
                </script>
            """, unsafe_allow_html=True)
            st.session_state.audio_loaded = True
        st.query_params.clear()

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

    st.markdown("<h1 style='text-align: center;'>气体检测计时器</h1>", unsafe_allow_html=True)

    # 音频初始化界面
    if not st.session_state.audio_initialized:
        st.markdown("<h3 style='text-align: center; color: #ff4b4b;'>请先初始化音频系统</h3>", unsafe_allow_html=True)
        init_col1, init_col2, init_col3 = st.columns([2, 1, 2])
        with init_col2:
            if st.button("初始化音频系统", key="init_audio", use_container_width=True, type="primary"):
                st.markdown("""
                    <script>
                    if (window.audioSystem) {
                        window.audioSystem.initialize();
                    }
                    </script>
                """, unsafe_allow_html=True)
                st.rerun()

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
                st.markdown("""
                    <script>
                    if (window.audioSystem) {
                        window.audioSystem.playSound('phase1');
                    }
                    </script>
                """, unsafe_allow_html=True)
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
            
            # 播放完成音效
            st.markdown("""
                <script>
                if (window.audioSystem) {
                    window.audioSystem.playSound('phase2');
                }
                </script>
            """, unsafe_allow_html=True)
            
            # 重置状态
            st.session_state.timer_running = False
            st.session_state.current_state = "就绪"
            st.session_state.phase = "待开始"
            st.session_state.sample_progress_value = 0
            st.session_state.zero_progress_value = 0
            st.rerun()

if __name__ == "__main__":
    main()
