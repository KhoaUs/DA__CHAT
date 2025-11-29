import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import streamlit as st

class DashboardRenderer:
    
    # --- HELPER: Parse Input ---
    @staticmethod
    def _parse_data(data_input):
        return json.loads(data_input) if isinstance(data_input, str) else data_input

    # --- 1. DASHBOARD GIÁ (Cập nhật) ---
    @staticmethod
    def render_price_dashboard(data_input):
        data = DashboardRenderer._parse_data(data_input)
        
        st.markdown("### 💰 Phân Tích Giá")
        
        # KPI Cards
        cols = st.columns(4)
        cols[0].metric("Thấp nhất", f"{data['summary']['lowest_price']:,} đ")
        cols[1].metric("Trung bình", f"{data['summary']['average_price']:,} đ")
        cols[2].metric("Cao nhất", f"{data['summary']['highest_price']:,} đ")
        cols[3].metric("Tin đăng", data['summary']['listing_count'])
        
        # Chart 1 & 2
        c1, c2 = st.columns(2)
        with c1:
            fig_bar = px.bar(x=data['current_price_by_platform']['labels'], 
                             y=data['current_price_by_platform']['data'], 
                             title="Giá trung bình theo Sàn", labels={'y':'VNĐ', 'x':'Sàn'},
                             color=data['current_price_by_platform']['labels'])
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            fig_pie = px.pie(names=data['price_distribution']['labels'], 
                             values=data['price_distribution']['data'], 
                             title="Phân bố khoảng giá", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        # [NEW] TOP CHEAPEST LISTINGS TABLE
        if "top_cheapest_listings" in data:
            st.subheader("🔥 Top 3 Deal Tốt Nhất")
            df_cheap = pd.DataFrame(data['top_cheapest_listings'])
            
            # Format lại bảng cho đẹp
            st.dataframe(
                df_cheap,
                column_config={
                    "listing_name": "Tên sản phẩm",
                    "price": st.column_config.NumberColumn("Giá bán", format="%d đ"),
                    "platform": "Sàn",
                    "url": st.column_config.LinkColumn("Link mua")
                },
                hide_index=True,
                use_container_width=True
            )

    # --- 2. DASHBOARD DOANH SỐ (Cập nhật) ---
    @staticmethod
    def render_sales_dashboard(data_input):
        data = DashboardRenderer._parse_data(data_input)
        
        st.markdown("### 📈 Phân Tích Doanh Số")
        st.metric("Tổng Doanh Thu Ước Tính", f"{data['summary']['total_revenue_estimate']:,} VNĐ", delta="All time")
        
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(names=data['sales_share_by_platform']['labels'], 
                             values=data['sales_share_by_platform']['data'], 
                             title="Thị Phần Theo Sàn (Số lượng)")
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            df_shop = pd.DataFrame(data['top_selling_shops_all_time'])
            fig_bar = px.bar(df_shop, x='total_sold', y='shop_name', orientation='h', title="Top Shop Bán Chạy")
            st.plotly_chart(fig_bar, use_container_width=True)

        # [NEW] SCATTER PLOT: PRICE VS SALES
        if "sales_vs_price_correlation" in data:
            st.markdown("#### 📉 Tương quan: Giá bán & Lượng mua")
            df_corr = pd.DataFrame(data['sales_vs_price_correlation'])
            
            fig_corr = px.scatter(
                df_corr, 
                x="price", 
                y="total_sold",
                size="total_sold", # Bong bóng càng to bán càng chạy
                color="listing_name",
                hover_name="listing_name",
                title="Liệu giá rẻ có bán chạy hơn?",
                labels={"price": "Giá bán", "total_sold": "Đã bán"}
            )
            st.plotly_chart(fig_corr, use_container_width=True)

    # --- 3. DASHBOARD ĐÁNH GIÁ (Cập nhật) ---
    @staticmethod
    def render_review_dashboard(data_input):
        data = DashboardRenderer._parse_data(data_input)
        
        st.markdown("### ⭐ Phân Tích Đánh Giá")
        
        c1, c2 = st.columns(2)
        c1.metric("Điểm trung bình", f"{data['summary']['average_rating']}/5")
        c2.metric("Tỉ lệ hài lòng", f"{data['summary']['positive_sentiment_percent']}%")
        
        # [NEW] WORD CLOUD / KEYWORDS ANALYSIS
        if "positive_keywords" in data and "negative_keywords" in data:
            st.markdown("#### 🗣️ Khách hàng đang nói gì?")
            k1, k2 = st.columns(2)
            
            with k1:
                st.caption("✅ Từ khóa tích cực")
                df_pos = pd.DataFrame(data['positive_keywords'])
                fig_pos = px.bar(df_pos, x='count', y='word', orientation='h', 
                                 title="", color_discrete_sequence=['#00CC96'])
                fig_pos.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, height=300)
                st.plotly_chart(fig_pos, use_container_width=True)
                
            with k2:
                st.caption("❌ Vấn đề thường gặp")
                df_neg = pd.DataFrame(data['negative_keywords'])
                fig_neg = px.bar(df_neg, x='count', y='word', orientation='h', 
                                 title="", color_discrete_sequence=['#EF553B'])
                fig_neg.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, height=300)
                st.plotly_chart(fig_neg, use_container_width=True)
        
        # Rating Distribution
        st.markdown("#### Phân bố sao")
        fig_dist = px.bar(x=data['rating_distribution']['labels'], 
                          y=data['rating_distribution']['data'], 
                          color=data['rating_distribution']['labels'])
        st.plotly_chart(fig_dist, use_container_width=True)

    # --- 4. COMBINED DASHBOARD ---
    @staticmethod
    def render_combined_dashboard(data_input):
        data = DashboardRenderer._parse_data(data_input)
        
        st.markdown(f"## 📊 Báo Cáo Toàn Diện: {data.get('product_name', 'Sản phẩm')}")
        
        tab1, tab2, tab3 = st.tabs(["💰 GIÁ & DEAL", "📈 DOANH SỐ & TREND", "⭐ REVIEW & INSIGHT"])
        
        with tab1:
            DashboardRenderer.render_price_dashboard(data['price_stats'])
        with tab2:
            DashboardRenderer.render_sales_dashboard(data['sales_stats'])
        with tab3:
            DashboardRenderer.render_review_dashboard(data['review_stats'])