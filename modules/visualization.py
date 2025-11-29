import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import streamlit as st

class DashboardRenderer:
    @staticmethod
    def render_price_dashboard(data_input):
        # Nếu input là string JSON thì parse, nếu là dict thì dùng luôn
        data = json.loads(data_input) if isinstance(data_input, str) else data_input
        
        # 1. KPI Cards
        cols = st.columns(4)
        cols[0].metric("Giá Thấp Nhất", f"{data['summary']['lowest_price']:,} đ")
        cols[1].metric("Giá Trung Bình", f"{data['summary']['average_price']:,} đ")
        cols[2].metric("Giá Cao Nhất", f"{data['summary']['highest_price']:,} đ")
        cols[3].metric("Số lượng tin đăng", data['summary']['listing_count'])
        
        # 2. Charts
        col1, col2 = st.columns(2)
        with col1:
            fig_bar = px.bar(
                x=data['current_price_by_platform']['labels'],
                y=data['current_price_by_platform']['data'],
                title="Giá trung bình theo sàn",
                labels={'x': 'Sàn', 'y': 'Giá (VNĐ)'},
                color=data['current_price_by_platform']['labels']
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col2:
            fig_pie = px.pie(
                names=data['price_distribution']['labels'],
                values=data['price_distribution']['data'],
                title="Phân bố khoảng giá",
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    @staticmethod
    def render_sales_dashboard(data_input):
        data = json.loads(data_input) if isinstance(data_input, str) else data_input
        
        st.metric("Tổng doanh thu ước tính", f"{data['summary']['total_revenue_estimate']:,} VNĐ")
        
        col1, col2 = st.columns(2)
        with col1:
            # Biểu đồ tròn thị phần
            fig_pie = px.pie(
                names=data['sales_share_by_platform']['labels'],
                values=data['sales_share_by_platform']['data'],
                title="Thị phần doanh số (Số lượng bán)",
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col2:
            # Biểu đồ Top Shop
            shops = data['top_selling_shops_all_time']
            df_shop = pd.DataFrame(shops)
            fig_shop = px.bar(df_shop, x='total_sold', y='shop_name', orientation='h', title="Top Shop bán chạy")
            st.plotly_chart(fig_shop, use_container_width=True)

    @staticmethod
    def render_review_dashboard(data_input):
        data = json.loads(data_input) if isinstance(data_input, str) else data_input
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Điểm đánh giá trung bình", f"{data['summary']['average_rating']}/5", delta=f"{data['summary']['total_reviews']} đánh giá")
            fig_sent = px.pie(
                names=data['sentiment_analysis']['labels'],
                values=data['sentiment_analysis']['data'],
                title="Phân tích cảm xúc",
                color_discrete_map={"Tích cực": "green", "Tiêu cực": "red", "Trung tính": "gray"}
            )
            st.plotly_chart(fig_sent, use_container_width=True)
            
        with col2:
            fig_dist = px.bar(
                x=data['rating_distribution']['labels'],
                y=data['rating_distribution']['data'],
                title="Phân bố sao"
            )
            st.plotly_chart(fig_dist, use_container_width=True)

    @staticmethod
    def render_combined_dashboard(data_input):
        data = json.loads(data_input) if isinstance(data_input, str) else data_input
        
        st.header(f"Báo Cáo Toàn Diện: {data.get('product_name', 'Sản phẩm')}")
        
        # Tạo 3 tab
        tab1, tab2, tab3 = st.tabs(["💰 Giá Cả", "📈 Doanh Số", "⭐ Đánh Giá"])
        
        with tab1:
            DashboardRenderer.render_price_dashboard(data['price_stats'])
        
        with tab2:
            DashboardRenderer.render_sales_dashboard(data['sales_stats'])
            
        with tab3:
            DashboardRenderer.render_review_dashboard(data['review_stats'])