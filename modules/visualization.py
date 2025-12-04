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

    # --- 1. RENDER TOP BRANDS ---
    @staticmethod
    def render_top_brands(data_list):
        if not data_list: return
        df = pd.DataFrame(data_list)
        
        st.markdown("### 🏆 Top Thương Hiệu (Theo Doanh Thu)")
        
        # Vẽ biểu đồ cột ngang
        fig = px.bar(df, x='value', y='brand', color='platform', orientation='h',
                     title="Thị phần thương hiệu theo sàn",
                     labels={'value': 'Doanh thu ước tính', 'brand': 'Thương hiệu'},
                     text_auto='.2s')
        
        fig.update_layout(yaxis={'categoryorder':'total ascending'}) # Sắp xếp tăng dần
        st.plotly_chart(fig, use_container_width=True)

    # --- 2. RENDER SELLER DIVERSITY ---
    @staticmethod
    def render_seller_diversity(data_list):
        if not data_list: return
        df = pd.DataFrame(data_list)
        
        st.markdown("### 🏪 Phân Tích Đa Dạng Seller")
        st.caption("Chỉ số Diversity cao thể hiện Shop bán nhiều loại mặt hàng khác nhau.")
        
        # Scatter Plot: Trục X = Product Count, Trục Y = Diversity Index
        fig = px.scatter(df, x='product_count', y='diversity_index',
                         size='unique_categories', color='platform',
                         hover_name='seller_name',
                         title="Quy mô Shop vs Độ đa dạng danh mục",
                         labels={'product_count': 'Tổng sản phẩm', 'diversity_index': 'Chỉ số đa dạng'})
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Table Top Seller
        with st.expander("Xem chi tiết danh sách Seller"):
            st.dataframe(df[['seller_name', 'platform', 'diversity_index', 'unique_categories']], use_container_width=True)

    # --- 3. RENDER PRICE RANGE (BOX PLOT) ---
    @staticmethod
    def render_price_range(data_list):
        if not data_list: return
        # Vì dữ liệu đã tính sẵn Q1, Median... nên dùng graph_objects.Box
        
        st.markdown("### 🕯️ Cấu Trúc Giá (Price Range)")
        
        fig = go.Figure()
        
        # Group by Platform + Category để vẽ
        # Ở đây demo vẽ theo từng dòng dữ liệu
        for item in data_list:
            label = f"{item['platform']} - {item['categories']}"
            fig.add_trace(go.Box(
                name=label,
                q1=[item['q_low']], 
                median=[item['median_price']],
                q3=[item['q_high']], 
                lowerfence=[item['min_price']],
                upperfence=[item['max_price']],
                marker_color='#1f77b4' if item['platform'] == 'Shopee' else '#ff7f0e'
            ))
            
        fig.update_layout(title="Phân bố dải giá theo Sàn & Danh mục", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # --- 4. RENDER ROI ---
    @staticmethod
    def render_roi_stats(data_list):
        if not data_list: return
        df = pd.DataFrame(data_list)
        
        st.markdown("### 💰 Hiệu Suất ROI (Sold / Price)")
        st.caption("Chỉ số thể hiện: Với mỗi đồng giá bán ra, thu lại bao nhiêu lượt mua.")
        
        # Vẽ biểu đồ Group Bar để so sánh Mean vs Median
        fig = go.Figure()
        fig.add_trace(go.Bar(name='ROI Trung Bình', x=df['group'], y=df['roi_mean']))
        fig.add_trace(go.Bar(name='ROI Trung Vị', x=df['group'], y=df['roi_median']))
        
        fig.update_layout(barmode='group', title="So sánh hiệu quả ROI theo nhóm")
        st.plotly_chart(fig, use_container_width=True)

    # --- 5. RENDER ADVANCED DASHBOARD (TỔNG HỢP) ---
    @staticmethod
    def render_advanced_dashboard(data_input):
        data = DashboardRenderer._parse_data(data_input)
        
        st.header(f"🚀 Báo Cáo Chuyên Sâu: {data.get('keyword', 'Thị trường')}")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🏆 Thương Hiệu", "🏪 Đối Thủ", "🕯️ Phân Khúc Giá", "💰 Hiệu Quả (ROI)"])
        
        with tab1:
            DashboardRenderer.render_top_brands(data.get('top_brands'))
        with tab2:
            DashboardRenderer.render_seller_diversity(data.get('seller_diversity'))
        with tab3:
            DashboardRenderer.render_price_range(data.get('price_range'))
        with tab4:
            DashboardRenderer.render_roi_stats(data.get('roi_stats'))


     # --- 5. TOP SELLERS VISUALIZATION ---
    @staticmethod
    def render_top_sellers_dashboard(data_input):
        """
        Visualize the output of top_sellers(): top sellers by value,
        platform share, and a sortable table. Expected schema:
        {
          "data": [ {"rank": int, "seller_name": str, "platform": str, "value": number}, ... ],
          "meta": {"filters": {"by": "sold"|"product_count"}, ...}
        }
        """
        raw = DashboardRenderer._parse_data(data_input)
        rows = raw.get('data', raw)
        if not rows:
            st.info("Không có dữ liệu người bán để hiển thị.")
            return

        df = pd.DataFrame(rows)
        required_cols = {"rank", "seller_name", "platform", "value"}
        if not required_cols.issubset(df.columns):
            st.warning("Dữ liệu không đúng định dạng mong đợi cho top_sellers().")
            st.write(df.head())
            return

        by = raw.get('meta', {}).get('filters', {}).get('by', 'product_count')
        metric_label = "Đã bán" if by == "sold" else "Số sản phẩm"

        st.markdown("### 🏪 Top Người Bán (Sellers)")

        # Overall
        df_sorted = df.sort_values(["value", "rank"], ascending=[False, True]).reset_index(drop=True)
        top_name = df_sorted.iloc[0]["seller_name"] if len(df_sorted) else "N/A"
        top_val = df_sorted.iloc[0]["value"] if len(df_sorted) else 0
        cols = st.columns(4)
        cols[0].metric("Top 1 Seller", str(top_name))
        cols[1].metric(metric_label, f"{int(top_val):,}")
        cols[2].metric("Số seller", f"{df['seller_name'].nunique():,}")
        cols[3].metric("Số sàn", f"{df['platform'].nunique():,}")

        # Charts
        c1, c2 = st.columns(2)
        with c1:
            # Horizontal bar of sellers
            fig_bar = px.bar(
                df_sorted.head(20),
                x="value",
                y="seller_name",
                orientation='h',
                color="platform",
                title=f"Top Sellers theo {metric_label}",
                labels={"value": metric_label, "seller_name": "Seller"},
                hover_data=["rank", "platform"]
            )
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            # Platform share among the top sellers
            plat_share = df.groupby('platform', as_index=False)['value'].sum()
            fig_pie = px.pie(
                plat_share,
                names='platform',
                values='value',
                title=f"Tỷ trọng theo sàn ({metric_label})",
                hole=0.35
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)



    # --- 6. BRAND SHARE CHART VISUALIZATION ---
    @staticmethod
    def render_brand_share_dashboard(data_input):
        """
        Visualize the output of brand_share_chart(): brand market share across platforms.
        Expected schema:
        {
          "data": [ {"platform": str, "brand": str, "value": number, "share_pct": float}, ... ],
          "meta": {"filters": {"metric": "sku"|"revenue_est", "normalize": bool}, ...}
        }
        """
        raw = DashboardRenderer._parse_data(data_input)
        rows = raw.get('data', raw)
        if not rows:
            st.info("Không có dữ liệu thương hiệu để hiển thị.")
            return

        df = pd.DataFrame(rows)
        required_cols = {"platform", "brand", "value"}
        if not required_cols.issubset(df.columns):
            st.warning("Dữ liệu không đúng định dạng mong đợi cho brand_share_chart().")
            st.write(df.head())
            return

        metric = raw.get('meta', {}).get('filters', {}).get('metric', 'sku')
        normalized = raw.get('meta', {}).get('filters', {}).get('normalize', True)
        metric_label = "Doanh Thu" if metric == "revenue_est" else "Số SKU"

        st.markdown("### 📊 Thị Phần Thương Hiệu")

        # Overall
        total_brands = df['brand'].nunique()
        total_platforms = df['platform'].nunique()
        top_brand = df.groupby('brand')['value'].sum().idxmax() if len(df) else "N/A"
        total_value = df['value'].sum()
        
        cols = st.columns(4)
        cols[0].metric("Tổng Thương Hiệu", f"{total_brands:,}")
        cols[1].metric("Số Sàn", f"{total_platforms:,}")
        cols[2].metric("Top Brand", str(top_brand))
        cols[3].metric(f"Tổng {metric_label}", f"{int(total_value):,}")

        # Charts
        c1, c2 = st.columns(2)
        
        with c1:
            # Stacked bar chart by platform
            fig_bar = px.bar(
                df,
                x="platform",
                y="share_pct" if normalized and 'share_pct' in df.columns else "value",
                color="brand",
                title=f"Thị Phần Thương Hiệu theo Sàn ({metric_label})",
                labels={
                    "value": metric_label,
                    "share_pct": "Tỷ lệ (%)",
                    "platform": "Sàn",
                    "brand": "Thương Hiệu"
                },
                barmode="stack"
            )
            if normalized and 'share_pct' in df.columns:
                fig_bar.update_yaxes(title="Tỷ lệ (%)")
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            # Overall brand share pie chart
            brand_totals = df.groupby('brand', as_index=False)['value'].sum()
            fig_pie = px.pie(
                brand_totals,
                names='brand',
                values='value',
                title=f"Tổng Thị Phần Thương Hiệu ({metric_label})",
                hole=0.4
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)