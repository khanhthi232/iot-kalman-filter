import streamlit as st
import numpy as np
import pandas as pd
import time
import plotly.graph_objects as go

st.set_page_config(page_title="Real-Time IoT Kalman Filter", layout="wide")

st.title("📡 Hệ thống Lọc Tín hiệu Cảm biến IoT Thời gian thực")
st.markdown("""
Ứng dụng tiếp nhận luồng dữ liệu cảm biến mô phỏng (bị nhiễu động học) và áp dụng **Bộ lọc Kalman** để ước lượng giá trị thực theo thời gian thực.
""")

# Khởi tạo tham số không gian trạng thái
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['Time', 'True', 'Measured', 'Kalman'])
    st.session_state.x_est = 20.0  # Nhiệt độ ban đầu
    st.session_state.p_est = 1.0   # Sai số ước lượng ban đầu
    st.session_state.true_val = 20.0

# Giao diện điều khiển
col1, col2 = st.columns([1, 3])
with col1:
    st.subheader("Tham số Bộ lọc")
    R = st.slider("Độ nhiễu đo lường (R)", 0.1, 10.0, 5.0, 0.1)
    Q = st.slider("Độ nhiễu hệ thống (Q)", 0.001, 1.0, 0.05, 0.001)
    speed = st.slider("Tốc độ luồng dữ liệu (giây)", 0.05, 0.5, 0.1, 0.05)
    start_btn = st.button("Bắt đầu luồng Real-Time", type="primary")

with col2:
    plot_placeholder = st.empty()
    metric_placeholder = st.empty()

# Vòng lặp xử lý Real-Time
if start_btn:
    # Mô phỏng nhận 150 điểm dữ liệu liên tục
    for _ in range(150):
        # 1. Sinh dữ liệu thực tế (Random walk) và Dữ liệu đo lường (Có nhiễu R)
        st.session_state.true_val += np.random.normal(0, 0.2)
        measurement = st.session_state.true_val + np.random.normal(0, np.sqrt(R))

        # 2. Thuật toán Kalman Filter 1D
        # Pha dự đoán (Predict)
        x_pred = st.session_state.x_est
        p_pred = st.session_state.p_est + Q

        # Pha cập nhật (Update)
        K = p_pred / (p_pred + R)
        st.session_state.x_est = x_pred + K * (measurement - x_pred)
        st.session_state.p_est = (1 - K) * p_pred

        # 3. Lưu trữ dữ liệu vào DataFrame
        new_row = {
            'Time': pd.Timestamp.now(), 
            'True': st.session_state.true_val, 
            'Measured': measurement, 
            'Kalman': st.session_state.x_est
        }
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
        
        # Giữ lại 100 điểm dữ liệu gần nhất để tối ưu bộ nhớ UI
        if len(st.session_state.data) > 100:
            st.session_state.data = st.session_state.data.iloc[-100:]

        # 4. Cập nhật biểu đồ Real-Time bằng Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=st.session_state.data['Time'], y=st.session_state.data['Measured'], 
                                 mode='markers', name='Cảm biến thô (Nhiễu)', marker=dict(color='rgba(200, 200, 200, 0.8)', size=6)))
        fig.add_trace(go.Scatter(x=st.session_state.data['Time'], y=st.session_state.data['True'], 
                                 mode='lines', name='Giá trị thực tế', line=dict(color='green', dash='dot')))
        fig.add_trace(go.Scatter(x=st.session_state.data['Time'], y=st.session_state.data['Kalman'], 
                                 mode='lines', name='Bộ lọc Kalman', line=dict(color='red', width=3)))

        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_title="Thời gian (Live)", yaxis_title="Nhiệt độ (°C)",
            height=450, showlegend=True
        )
        
        # Hiển thị trực tiếp (ghi đè lên placeholder)
        plot_placeholder.plotly_chart(fig, use_container_width=True)
        
        with metric_placeholder.container():
            m1, m2, m3 = st.columns(3)
            m1.metric("Cảm biến đo được", f"{measurement:.2f} °C")
            m2.metric("Kết quả lọc Kalman", f"{st.session_state.x_est:.2f} °C")
            m3.metric("Hệ số Kalman (K)", f"{K:.4f}")

        # Độ trễ mạng mô phỏng
        time.sleep(speed)
