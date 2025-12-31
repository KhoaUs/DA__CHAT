import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import numpy as np
import streamlit as st

# --- CẤU HÌNH UI ---
THEME_COLORS = {
    "primary": "#FF4B4B",
    "secondary": "#F0F2F6",
    "positive": "#00CC96",  # Xanh lá
    "neutral": "#FFD700",   # Vàng
    "negative": "#EF553B"   # Đỏ
}

class DashboardRenderer:
    
    @staticmethod
    def _parse_data(data_input):
        if isinstance(data_input, str):
            try:
                data_input = json.loads(data_input)
            except Exception:
                return data_input
        if isinstance(data_input, dict) and "data" in data_input:
            return data_input["data"]
        return data_input

    @staticmethod
    def _render_kpi_card(title, value, icon, color="#f0f2f6"):
        st.markdown(f"""
        <div style="background-color: {color}; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; border: 1px solid #eee;">
            <div style="font-size: 1.5rem;">{icon}</div>
            <p style="color: #666; font-size: 0.85rem; margin: 0;">{title}</p>
            <h4 style="color: #333; margin: 5px 0; font-weight: 700;">{value}</h4>
        </div>
        """, unsafe_allow_html=True)

    # --- 1. PRICE DASHBOARD ---
    @staticmethod
    def render_price_dashboard(data_input):
        data = DashboardRenderer._parse_data(data_input)
        if not data:
            st.warning("Không có dữ liệu giá.")
            return

        df = pd.DataFrame(data)
        st.markdown("### 💰 Thống Kê Giá")

        if 'platform' in df.columns:
            total_count = df['count'].sum()
            avg_price = (df['mean_price'] * df['count']).sum() / total_count if total_count else 0
            min_price = df['min_price'].min()
            max_price = df['max_price'].max()
        else:
            avg_price = df['mean_price'].iloc[0]
            min_price = df['min_price'].iloc[0]
            max_price = df['max_price'].iloc[0]

        # KPI Cards
        c1, c2, c3 = st.columns(3)
        with c1: DashboardRenderer._render_kpi_card("Rẻ Nhất", f"{min_price:,.0f} ₫", "📉")
        with c2: DashboardRenderer._render_kpi_card("Trung Bình", f"{avg_price:,.0f} ₫", "⚖️", "#fff3e0")
        with c3: DashboardRenderer._render_kpi_card("Đắt Nhất", f"{max_price:,.0f} ₫", "📈")

        st.markdown("---")

        if 'platform' in df.columns:
            col1, col2 = st.columns([2, 1])
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df['platform'], y=df['mean_price'],
                    name='Giá TB', marker_color='#636EFA',
                    text=df['mean_price'], texttemplate='%{text:,.0f}', textposition='auto',
                    error_y=dict(type='data', array=df['max_price']-df['mean_price'], arrayminus=df['mean_price']-df['min_price'], visible=True, color='gray')
                ))
                fig.update_layout(title="So sánh Giá & Biên độ dao động", template="plotly_white", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig_pie = px.pie(df, values='count', names='platform', title='Nguồn hàng', hole=0.6)
                fig_pie.update_layout(template="plotly_white", showlegend=False)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
                
            fig_box = go.Figure()
            for _, row in df.iterrows():
                fig_box.add_trace(go.Box(
                    name=row['platform'], q1=[row['q10']], median=[row['median_price']], q3=[row['q90']],
                    lowerfence=[row['min_price']], upperfence=[row['max_price']], orientation='h', boxpoints=False
                ))
            fig_box.update_layout(title="Phân khúc giá chi tiết", height=250, template="plotly_white", margin=dict(t=30,b=20))
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            fig = go.Figure(go.Indicator(
                mode = "number+gauge", value = avg_price,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Giá Trung Bình Thị Trường"},
                gauge = {'axis': {'range': [min_price*0.8, max_price*1.1]}, 'bar': {'color': "#636EFA"}}
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)

    # --- 2. SALES DASHBOARD ---
    @staticmethod
    def render_sales_dashboard(data_input):
        data = DashboardRenderer._parse_data(data_input)
        if not data: return
        
        raw_items = data.get("raw_items", [])
        sellers_data = data.get("top_sellers", [])

        st.markdown("### 📈 Phân Tích Doanh Số")

        if raw_items:
            df = pd.DataFrame(raw_items)
            df = df[df['price'] > 0] 
            
            if not df.empty:
                df['revenue'] = df['price'] * df['sold']
                total_rev = df['revenue'].sum()
                total_sold = df['sold'].sum()
                
                k1, k2 = st.columns(2)
                with k1: st.metric("Tổng Doanh Thu (Ước tính)", f"{total_rev:,.0f} ₫", help="Tính trên tập mẫu tìm thấy")
                with k2: st.metric("Tổng Sản Lượng", f"{total_sold:,.0f} cái")
                
                if total_rev > 0:
                    st.markdown("#### 🗺️ Bản Đồ Doanh Thu (Treemap)")
                    df_tree = df.groupby(['platform', 'seller_name'])['revenue'].sum().reset_index()
                    df_tree = df_tree.sort_values('revenue', ascending=False).head(20)
                    
                    fig_tree = px.treemap(
                        df_tree, path=[px.Constant("Thị trường"), 'platform', 'seller_name'], values='revenue',
                        color='platform', color_discrete_sequence=px.colors.qualitative.Prism
                    )
                    fig_tree.update_traces(root_color="lightgrey")
                    fig_tree.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=400)
                    st.plotly_chart(fig_tree, use_container_width=True)

                st.markdown("#### 💠 Tương quan Giá - Lượng bán")
                num_platforms = df['platform'].nunique()
                color_col = 'platform' if num_platforms > 1 else 'revenue'
                
                fig_scat = px.scatter(
                    df, x="price", y="sold", color=color_col, size="sold", size_max=50,
                    hover_name="product_name", hover_data={"price": ":,.0f", "revenue": ":,.0f"},
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                if num_platforms == 1: fig_scat.update_layout(coloraxis_colorbar=dict(title="Doanh thu"))
                
                fig_scat.update_layout(template="plotly_white", height=400, xaxis_title="Giá bán", yaxis_title="Số lượng bán")
                
                if df['sold'].max() == 0:
                    fig_scat.update_traces(marker=dict(size=10)) 
                    st.caption("⚠️ Lưu ý: Các sản phẩm này hiện chưa có lượt bán (Sold = 0).")
                    
                st.plotly_chart(fig_scat, use_container_width=True)

        if sellers_data:
            with st.expander("Danh sách Top Sellers chi tiết"):
                df_sell = pd.DataFrame(sellers_data).sort_values('value', ascending=False)
                st.dataframe(
                    df_sell[['seller_name', 'platform', 'value']],
                    column_config={"value": st.column_config.ProgressColumn("Lượt bán", format="%d", min_value=0, max_value=int(df_sell['value'].max()))},
                    use_container_width=True, hide_index=True
                )

    # --- 3. REVIEW DASHBOARD ---
    @staticmethod
    def render_review_dashboard(data_input):
        data = DashboardRenderer._parse_data(data_input)
        if not data: return
        df = pd.DataFrame(data)
        
        st.markdown("### ⭐ Phân Tích Đánh Giá")
        
        df['star_rating'] = ((df['bucket_left'] + df['bucket_right']) / 2).round().astype(int).clip(1, 5)
        def get_sentiment(star):
            if star >= 4: return 'Tích cực (4-5⭐)'
            elif star == 3: return 'Trung tính (3⭐)'
            else: return 'Tiêu cực (1-2⭐)'
        df['sentiment'] = df['star_rating'].apply(get_sentiment)
        
        SOFT_COLORS = {'Tích cực (4-5⭐)': '#66C2A5', 'Trung tính (3⭐)': '#FDC086', 'Tiêu cực (1-2⭐)': '#D53E4F'}
        total_reviews = df['count'].sum()
        df['mid_point'] = (df['bucket_left'] + df['bucket_right']) / 2
        avg_rating = (df['mid_point'] * df['count']).sum() / total_reviews if total_reviews else 0

        c1, c2 = st.columns([1.2, 1.8])
        with c1:
            gauge_color = SOFT_COLORS['Tích cực (4-5⭐)'] if avg_rating >= 4.0 else (SOFT_COLORS['Trung tính (3⭐)'] if avg_rating >= 3.0 else SOFT_COLORS['Tiêu cực (1-2⭐)'])
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = avg_rating,
                title = {'text': "Điểm Trung Bình", 'font': {'size': 18, 'color': '#555'}},
                number = {'font': {'size': 36, 'color': '#333'}},
                gauge = {'axis': {'range': [0, 5], 'tickwidth': 1}, 'bar': {'color': gauge_color, 'thickness': 0.8}, 'bgcolor': "white", 'steps': [{'range': [0, 5], 'color': '#F0F2F6'}]}
            ))
            fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)
            
        with c2:
            sent_counts = df.groupby('sentiment')['count'].sum().reset_index()
            fig_donut = px.pie(sent_counts, values='count', names='sentiment', hole=0.6, color='sentiment', color_discrete_map=SOFT_COLORS)
            fig_donut.update_layout(title=dict(text="Tỷ lệ hài lòng tổng thể", x=0), height=250, margin=dict(l=0, r=0, t=40, b=0), legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0))
            fig_donut.update_traces(textinfo='percent')
            fig_donut.add_annotation(text=f"{int(total_reviews)}<br>Reviews", x=0.5, y=0.5, font_size=15, showarrow=False, font_color="#666")
            st.plotly_chart(fig_donut, use_container_width=True)

        has_brand = df['brand'].notna().any()
        has_platform = 'platform' in df.columns
        sentiment_order = ['Tích cực (4-5⭐)', 'Trung tính (3⭐)', 'Tiêu cực (1-2⭐)']

        if has_brand:
            st.markdown("#### 🏢 Chất lượng theo Thương hiệu (Top 10)")
            top_brands = df.groupby('brand')['count'].sum().sort_values(ascending=False).head(10).index.tolist()
            df_final = df[df['brand'].isin(top_brands)].groupby(['brand', 'sentiment'])['count'].sum().reset_index()
            fig_bar = px.bar(
                df_final, y="brand", x="count", color="sentiment", orientation='h', barmode='group',
                color_discrete_map=SOFT_COLORS, category_orders={"sentiment": sentiment_order}, text_auto='.2s'
            )
            fig_bar.update_layout(template="plotly_white", height=400 + (len(top_brands) * 30), xaxis_title="Số lượng đánh giá", yaxis_title="", margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_bar, use_container_width=True)
        elif has_platform:
            st.markdown("#### 🛒 Chất lượng theo Sàn")
            df_plat = df.groupby(['platform', 'sentiment'])['count'].sum().reset_index()
            fig_bar = px.bar(
                df_plat, x="platform", y="count", color="sentiment", barmode='group',
                color_discrete_map=SOFT_COLORS, category_orders={"sentiment": sentiment_order}, text_auto=True
            )
            fig_bar.update_layout(template="plotly_white", height=400, xaxis_title="Sàn", yaxis_title="Số lượng đánh giá", margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_bar, use_container_width=True)

    # --- 4. TOP BRANDS DASHBOARD ---
    @staticmethod
    def render_top_brands(data_input):
        data = DashboardRenderer._parse_data(data_input)
        if isinstance(data, list): data = {'top_brands': data}
        if not data:
            st.warning("Không tìm thấy dữ liệu thương hiệu.")
            return

        top_brands_data = data.get('top_brands', [])
        brand_share_data = data.get('brand_share', [])
        rank_by = data.get('rank_by', 'revenue_est')
        rank_label = "Doanh thu" if rank_by == 'revenue_est' else "Sản lượng"
        
        if not top_brands_data:
            st.info("Chưa có dữ liệu.")
            return

        df = pd.DataFrame(top_brands_data)
        
        # Spotlight Top 1
        df_grouped = df.groupby('brand')['value'].sum().reset_index().sort_values('value', ascending=False)
        if not df_grouped.empty:
            leader = df_grouped.iloc[0]
            leader_share = (leader['value'] / df_grouped['value'].sum()) * 100
            
            st.markdown(f"### 👑 Nhà Vua: **{leader['brand']}**")
            c1, c2 = st.columns(2)
            with c1: DashboardRenderer._render_kpi_card(f"Thống lĩnh {rank_label}", f"{leader['value']:,.0f}" if rank_by == 'sold' else f"{leader['value']:,.0f} ₫", "💎", "#e3f2fd")
            with c2: DashboardRenderer._render_kpi_card("Thị phần nắm giữ", f"{leader_share:.1f}%", "🍰", "#fff3e0")
            
            leader_breakdown = df[df['brand'] == leader['brand']]
            if not leader_breakdown.empty:
                st.caption(f"Nguồn thu của **{leader['brand']}**:")
                fig_leader = px.bar(leader_breakdown, x='value', y='brand', color='platform', orientation='h', text_auto='.2s', height=100)
                fig_leader.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), yaxis=dict(visible=False), showlegend=True)
                st.plotly_chart(fig_leader, use_container_width=True)

        st.markdown("---")

        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.markdown("#### 📊 Top 10 Thương hiệu")
            df_top_10 = df.sort_values('value', ascending=True).tail(10)
            fig_bar = px.bar(df_top_10, x='value', y='brand', color='platform', orientation='h', text_auto='.2s')
            fig_bar.update_layout(template="plotly_white", height=450, xaxis_title=rank_label, yaxis_title="", legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_right:
            st.markdown("#### 🍰 Cấu trúc thị phần")
            if brand_share_data:
                df_share = pd.DataFrame(brand_share_data)
                brand_sums = df_share.groupby('brand')['value'].sum().sort_values(ascending=False)
                top_5_brands = brand_sums.head(5).index.tolist()
                df_share.loc[~df_share['brand'].isin(top_5_brands), 'brand'] = 'Khác'
                df_clean = df_share.groupby(['platform', 'brand'], as_index=False)['value'].sum()
                
                fig_sun = px.sunburst(df_clean, path=['platform', 'brand'], values='value', color='platform', color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_sun.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=400)
                st.plotly_chart(fig_sun, use_container_width=True)
            else:
                st.info("Thiếu dữ liệu thị phần.")

        with st.expander(f"🔎 Xem bảng xếp hạng đầy đủ"):
            st.dataframe(
                df[['rank', 'brand', 'platform', 'value']].sort_values('value', ascending=False),
                column_config={"value": st.column_config.ProgressColumn(rank_label, format="%d" if rank_by == 'sold' else "%.0f", min_value=0, max_value=int(df['value'].max()))},
                use_container_width=True, hide_index=True
            )

    # --- 5. ADVANCED DASHBOARD ---
    @staticmethod
    def render_advanced_dashboard(data_input):
        data = DashboardRenderer._parse_data(data_input)
        if not data:
            st.warning("Dữ liệu phân tích chuyên sâu chưa sẵn sàng.")
            return

        keyword = data.get('keyword', 'Sản phẩm')
        st.header(f"🚀 Phân Tích Chuyên Sâu: {keyword}")
        
        top_brands = pd.DataFrame(data.get('top_brands', []))
        seller_div = pd.DataFrame(data.get('seller_diversity', []))
        price_range = pd.DataFrame(data.get('price_range', []))
        roi_stats = pd.DataFrame(data.get('roi_stats', []))

        m1, m2, m3, m4 = st.columns(4)
        with m1: 
            total_rev = top_brands['value'].sum() if not top_brands.empty and 'value' in top_brands else 0
            DashboardRenderer._render_kpi_card("Quy mô mẫu", f"{total_rev:,.0f} ₫", "💰", "#e3f2fd")
        with m2:
            avg_market_price = price_range['median_price'].mean() if not price_range.empty else 0
            DashboardRenderer._render_kpi_card("Giá tham chiếu", f"{avg_market_price:,.0f} ₫", "🏷️", "#fff3e0")
        with m3:
            dominant_platform = top_brands.groupby('platform')['value'].sum().idxmax() if not top_brands.empty else "N/A"
            DashboardRenderer._render_kpi_card("Sàn thống trị", f"{dominant_platform}", "👑", "#e8f5e9")
        with m4:
            avg_roi = (roi_stats['roi_mean'].mean() * 1_000_000) if not roi_stats.empty else 0
            DashboardRenderer._render_kpi_card("Chỉ số Viral", f"{avg_roi:.1f} điểm", "🔥", "#ffebee")

        st.markdown("---")
        t1, t2, t3, t4 = st.tabs(["🗺️ Định Vị", "♟️ Chiến Lược", "⚖️ Cấu Trúc Giá", "💡 Hiệu Suất"])

        with t1:
            if not top_brands.empty:
                fig_tree = px.treemap(top_brands, path=[px.Constant("Thị trường"), 'platform', 'brand'], values='value', color='value', color_continuous_scale='Blues', title="Thị phần Doanh thu")
                fig_tree.update_traces(root_color="lightgrey")
                fig_tree.update_layout(template="plotly_white", margin=dict(t=30, l=0, r=0, b=0))
                st.plotly_chart(fig_tree, use_container_width=True)
            else: st.warning("Chưa đủ dữ liệu.")

        with t2:
            if not seller_div.empty:
                mean_div = seller_div['diversity_index'].mean()
                mean_count = seller_div['product_count'].mean()
                fig_quad = px.scatter(seller_div, x='product_count', y='diversity_index', color='platform', size='unique_categories', hover_name='seller_name', size_max=40, text='seller_name', title="Quy mô vs Đa dạng")
                fig_quad.add_vline(x=mean_count, line_dash="dash", line_color="grey")
                fig_quad.add_hline(y=mean_div, line_dash="dash", line_color="grey")
                fig_quad.update_traces(textposition='top center')
                fig_quad.update_layout(template="plotly_white", height=500, xaxis_title="Số lượng SP", yaxis_title="Diversity Index")
                st.plotly_chart(fig_quad, use_container_width=True)
            else: st.warning("Chưa đủ dữ liệu.")

        with t3:
            if not price_range.empty:
                fig_vio = go.Figure()
                for _, row in price_range.iterrows():
                    fig_vio.add_trace(go.Box(name=row['platform'], q1=[row['q_low']], median=[row['median_price']], q3=[row['q_high']], lowerfence=[row['min_price']], upperfence=[row['max_price']], orientation='h'))
                fig_vio.update_layout(title="Dải giá chấp nhận được", xaxis_title="VNĐ", template="plotly_white", height=400, showlegend=False)
                st.plotly_chart(fig_vio, use_container_width=True)
            else: st.warning("Chưa có dữ liệu giá.")

        with t4:
            if not roi_stats.empty:
                df_roi = roi_stats.copy()
                df_roi['roi_score'] = df_roi['roi_mean'] * 1_000_000
                df_roi = df_roi.sort_values('roi_score', ascending=True)
                def classify_roi(score):
                    if score > 10: return "🔥 Siêu Viral"
                    elif score > 1: return "✅ Ổn định"
                    else: return "🐢 Kén khách"
                df_roi['label'] = df_roi['roi_score'].apply(classify_roi)
                fig_bar = px.bar(df_roi, y='group', x='roi_score', color='label', orientation='h', text_auto='.1f', color_discrete_map={"🔥 Siêu Viral": "#00CC96", "✅ Ổn định": "#636EFA", "🐢 Kén khách": "#EF553B"})
                fig_bar.update_layout(template="plotly_white", xaxis_title="Điểm Viral", height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
            else: st.warning("Chưa đủ dữ liệu.")

    # --- 6. CATEGORY TRENDS DASHBOARD ---
    @staticmethod
    def render_category_trends(data_input):
        data = DashboardRenderer._parse_data(data_input)
        chart_data = data.get("data", []) if isinstance(data, dict) else data
        if not chart_data: 
            st.warning("Không tìm thấy dữ liệu xu hướng danh mục.")
            return

        st.header("🗂️ Phân Tích Cấu Trúc Ngành Hàng")
        df = pd.DataFrame(chart_data)
        if 'product_count' in df.columns: df = df.rename(columns={'product_count': 'Category', 'count': 'Volume'})
        
        df = df.sort_values('Volume', ascending=False)
        total_vol = df['Volume'].sum()
        df['Share'] = (df['Volume'] / total_vol) * 100
        df['Cumulative Share'] = df['Share'].cumsum()

        top_cat = df.iloc[0]
        c1, c2, c3 = st.columns(3)
        with c1: DashboardRenderer._render_kpi_card("Tổng mẫu", f"{total_vol}", "📦", "#e3f2fd")
        with c2: DashboardRenderer._render_kpi_card("Top 1", f"{top_cat['Category']}", "🏆", "#fff3e0")
        with c3: DashboardRenderer._render_kpi_card("Thị phần Top 1", f"{top_cat['Share']:.1f}%", "🍰", "#e8f5e9")

        st.markdown("---")
        t1, t2 = st.tabs(["🗺️ Bản Đồ Thị Phần", "📊 Pareto (80/20)"])

        with t1:
            fig_tree = px.treemap(df, path=[px.Constant("Tất cả"), 'Category'], values='Volume', color='Volume', color_continuous_scale='Blues', custom_data=['Share'])
            fig_tree.update_traces(hovertemplate='<b>%{label}</b><br>SL: %{value}<br>Thị phần: %{customdata[0]:.1f}%', textinfo="label+value")
            fig_tree.update_layout(template="plotly_white", margin=dict(t=0, l=0, r=0, b=0), height=450)
            st.plotly_chart(fig_tree, use_container_width=True)

        with t2:
            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Bar(x=df['Category'], y=df['Volume'], name='Số lượng', marker_color='#636EFA', text=df['Share'].apply(lambda x: f"{x:.1f}%"), textposition='auto'))
            fig_pareto.add_trace(go.Scatter(x=df['Category'], y=df['Cumulative Share'], name='Tỉ lệ tích lũy', yaxis='y2', mode='lines+markers', line=dict(color='#EF553B', width=3)))
            fig_pareto.update_layout(template="plotly_white", height=500, xaxis=dict(title="Danh mục"), yaxis=dict(title="Số lượng"), yaxis2=dict(title="Tỉ lệ (%)", overlaying='y', side='right', range=[0, 110], showgrid=False), legend=dict(orientation="h", y=1.1))
            fig_pareto.add_hline(y=80, line_dash="dash", line_color="gray", annotation_text="Giới hạn 80%", yref="y2")
            st.plotly_chart(fig_pareto, use_container_width=True)

    # --- 7. COMBINED DASHBOARD ---
    @staticmethod
    def render_combined_dashboard(data_input):
        data = DashboardRenderer._parse_data(data_input)
        st.subheader(f"📊 Báo cáo tổng hợp: {data.get('product_name', '')}")
        t1, t2, t3 = st.tabs(["💰 Giá Cả", "📈 Doanh Số", "⭐ Đánh Giá"])
        with t1: DashboardRenderer.render_price_dashboard(data.get('price_stats'))
        with t2: DashboardRenderer.render_sales_dashboard(data.get('sales_stats'))
        with t3: DashboardRenderer.render_review_dashboard(data.get('review_stats'))