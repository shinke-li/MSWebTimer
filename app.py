import streamlit as st
import time
from datetime import datetime

def notify_user():
    # 创建通知和震动脚本
    notification_script = """
        <script>
            function notify() {
                // 尝试震动
                if ('vibrate' in navigator) {
                    navigator.vibrate([200, 100, 200, 100, 200]);
                }
                
                // 播放系统提示音
                try {
                    const context = new (window.AudioContext || window.webkitAudioContext)();
                    const oscillator = context.createOscillator();
                    const gainNode = context.createGain();
                    
                    oscillator.connect(gainNode);
                    gainNode.connect(context.destination);
                    
                    oscillator.type = 'sine';
                    oscillator.frequency.value = 800;
                    gainNode.gain.value = 0.5;
                    
                    oscillator.start();
                    setTimeout(() => {
                        oscillator.stop();
                        setTimeout(() => {
                            oscillator.frequency.value = 600;
                            oscillator.start();
                            setTimeout(() => {
                                oscillator.stop();
                                setTimeout(() => {
                                    oscillator.frequency.value = 800;
                                    oscillator.start();
                                    setTimeout(() => oscillator.stop(), 200);
                                }, 100);
                            }, 200);
                        }, 100);
                    }, 200);
                } catch(e) {
                    console.error('Error playing sound:', e);
                }
            }
            
            // 立即执行三次
            notify();
            setTimeout(notify, 500);
            setTimeout(notify, 1000);
        </script>
    """
    return notification_script

def main():
    # 设置页面宽度
    st.set_page_config(layout="wide")
    
    # 页面标题居中
    st.markdown("<h1 style='text-align: center;'>气体检测计时器</h1>", unsafe_allow_html=True)
    
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
    if 'notify' not in st.session_state:
        st.session_state.notify = False
        
    # 输入参数
    col1, col2 = st.columns(2)
    with col1:
        zero_gas_time = st.number_input("零气时间(秒)", value=50, min_value=1)
        zero_gas_count = st.number_input("零气计数", value=2, min_value=1)
    with col2:
        sample_gas_time = st.number_input("气袋时间(秒)", value=50, min_value=1)
        sample_gas_count = st.number_input("气袋计数", value=3, min_value=1)
    
    # 状态显示 - 使用大字体居中显示
    st.markdown(f"<h2 style='text-align: center;'>状态: {st.session_state.current_state}</h2>", unsafe_allow_html=True)
    
    # 使用容器使进度条变宽
    with st.container():
        st.markdown("### 气袋检测进度")
        sample_progress = st.progress(st.session_state.sample_progress_value)
        st.markdown("### 零气清洗进度")
        zero_progress = st.progress(st.session_state.zero_progress_value)
    
    # 时间显示 - 居中
    time_display = st.empty()
    
    # 声音通知处理
    notification_placeholder = st.empty()
    if st.session_state.notify:
        notification_placeholder.markdown(notify_user(), unsafe_allow_html=True)
        st.session_state.notify = False
    
    # 居中的按钮列
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        button_style = """
        <style>
        div.stButton > button {
            font-size: 24px;
            height: 60px;
        }
        @media (max-width: 768px) {
            div.stButton > button {
                font-size: 20px;
                height: 50px;
                width: 100% !important;
            }
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
            
            # 气袋检测完成，触发通知
            st.session_state.notify = True
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
            
            # 清洗完成，触发通知
            st.session_state.notify = True
            
            # 重置所有状态
            st.session_state.timer_running = False
            st.session_state.current_state = "就绪"
            st.session_state.phase = "待开始"
            st.session_state.sample_progress_value = 0
            st.session_state.zero_progress_value = 0
            st.rerun()

if __name__ == "__main__":
    main()
