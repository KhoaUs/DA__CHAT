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