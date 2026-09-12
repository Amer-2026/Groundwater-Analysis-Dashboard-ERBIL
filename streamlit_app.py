        download_link = f'<a href="data:text/csv;base64,{b64}" download="{filename}" style="background-color:#ffffff;color:#1a0a2e;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:600;font-size:13px;border:1px solid #ddd;box-shadow:0 2px 8px rgba(0,0,0,0.15);display:inline-block;font-family:sans-serif;">📥 Download as CSV</a>'

        fig.add_annotation(
            x=0.98,
            y=0.98,
            xref="paper",
            yref="paper",
            text=download_link,
            showarrow=False,
            font=dict(size=13),
            bgcolor="rgba(0,0,0,0)",
            borderpad=0,
            xanchor="right",
            yanchor="top",
        )

    fig.update_layout(
        title=t("time_series_title", parameter=t(parameter), lat=f"{lat:.4f}", lon=f"{lon:.4f}"),
        xaxis=dict(
            title=t("date"),
            tickmode="array",
            tickvals=x_numeric,
            ticktext=months,
            tickangle=45,
            showgrid=True,
        ),
        yaxis=dict(title=t(parameter), showgrid=True, zeroline=True),
        template="plotly_white",
        height=263,
        margin=dict(t=50, b=80, l=50, r=50),
    )
    return fig


def create_regional_summary_plot(summary_data, parameter, csv_data=None, filename=None, button_text="📥 Download as CSV"):
    """Create regional summary bar chart with optional download button as annotation"""
    import base64

    df = pd.DataFrame(summary_data)
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title=t("no_data_location"),
            xaxis_title=t("date"),
            yaxis_title=t(parameter),
            height=263,
        )
        return fig

    months_lbl = [d.strftime("%Y-%m") for d in df["date"]]

    fig = go.Figure(
        go.Bar(x=months_lbl, y=df["mean"], marker_color="#B429F9")
    )

    # Create download button as HTML annotation (overlay on chart)
    if csv_data and filename:
        b64 = base64.b64encode(csv_data).decode()
        download_link = f'<a href="data:text/csv;base64,{b64}" download="{filename}" style="background-color:#ffffff;color:#1a0a2e;padding:6px 14px;border-radius:6px;text-decoration:none;font-weight:600;font-size:13px;border:1px solid #ddd;box-shadow:0 2px 8px rgba(0,0,0,0.15);display:inline-block;font-family:sans-serif;">{button_text}</a>'

        fig.add_annotation(
            x=0.98,
            y=0.93,
            xref="paper",
            yref="paper",
            text=download_link,
            showarrow=False,
            font=dict(size=13),
            bgcolor="rgba(0,0,0,0)",
            borderpad=0,
            xanchor="right",
            yanchor="top",
        )

    fig.update_layout(
        title=t("summary_title", parameter=t(parameter)),
        xaxis=dict(tickangle=45),
        template="plotly_white",
        height=263,
        margin=dict(t=50, b=80, l=50, r=50),
    )
    return fig


def to_csv_bytes(rows, value_col="value"):
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = df["date"].dt.strftime("%Y-%m")
    return df.to_csv(index=False).encode("utf-8")


# ==================== Main app ====================
def main():
    if "lang" not in st.session_state:
        st.session_state.lang = "en"

    if "selected_parameter" not in st.session_state:
        st.session_state.selected_parameter = "abstraction_mm"

    if "selected_date_str" not in st.session_state:
        st.session_state.selected_date_str = None

    if "regional_summary_data" not in st.session_state:
        st.session_state.regional_summary_data = None

    st.set_page_config(
        page_title=t("page_title"),
        page_icon="💧",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # ============================================================
    # ✅ INITIALIZE EARTH ENGINE FIRST — before any widget that calls
    # get_ee_assets(). st.stop() is deliberately OUTSIDE the try/except
    # so Streamlit's internal StopException cannot be swallowed.
    # ============================================================
    _ee_ok = False
    try:
        _ee_ok = initialize_ee()
    except Exception as e:
        st.error(f"{t('ee_init_critical')}: {str(e)}")
        st.error(traceback.format_exc())

    if not _ee_ok:
        st.error(t("ee_init_failed"))
        st.stop()
            
    # ---- DARK THEME CSS ----
    st.markdown(
        """
        <style>
        .stApp > header button { display: none !important; }
        header button { display: none !important; }
        header div:has(button) { display: none !important; }
        header [data-testid="stHeader"] [data-testid="stToolbar"] { display: none !important; }
        .st-emotion-cache-1h9usn1 { display: none !important; }
        .stApp > header {
            background: transparent !important;
            box-shadow: none !important;
            height: 0px !important;
            min-height: 0px !important;
            padding: 0px !important;
        }
        .stApp { margin-top: 0 !important; background-color: #0e1117 !important; }
        .main .block-container {
            padding-top: 0rem !important;
            padding-bottom: 1rem !important;
        }
        div[data-testid="stVerticalBlock"] { background-color: #0e1117 !important; }

        .banner {
            background: linear-gradient(135deg, 
                #0a0a2e 0%, #1a0533 10%, #2d1b69 20%, #4a1a8a 30%,
                #7b2fbe 40%, #B429F9 50%, #FF6B9D 60%, #FF9A9E 70%,
                #26C5F3 80%, #7B2FBE 90%, #4a1a8a 100%
            );
            padding: 2rem 4rem 1.5rem 4rem;
            margin: 0 !important;
            color: white;
            text-shadow: 0 2px 4px rgba(0,0,0,0.4);
            box-shadow: 0 4px 30px rgba(180, 41, 249, 0.3);
            position: relative;
            overflow: hidden;
            width: 100% !important;
            border-radius: 0;
            display: block;
        }
        .banner::before {
            content: '';
            position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            background: 
                radial-gradient(circle at 15% 25%, rgba(180, 41, 249, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 85% 75%, rgba(255, 107, 157, 0.08) 0%, transparent 35%),
                radial-gradient(circle at 45% 50%, rgba(38, 197, 243, 0.06) 0%, transparent 50%);
            pointer-events: none;
        }
        .banner-inner {
            display: flex; align-items: center; justify-content: space-between;
            flex-wrap: wrap; gap: 1rem; position: relative; z-index: 1;
            max-width: 1200px; margin: 0 auto;
        }
        .banner-title { flex: 1; min-width: 200px; text-align: left; }
        .banner-title h1 {
            font-size: 2rem; font-weight: 700; margin: 0; padding: 0;
            color: white;
            text-shadow: 0 2px 20px rgba(180, 41, 249, 0.5);
            text-align: left;
        }
        .banner-title .subtitle {
            font-size: 0.95rem; color: rgba(255,255,255,0.85);
            margin: 0.25rem 0 0 0; padding: 0; text-align: left;
        }
        .banner-title .welcome {
            font-size: 0.9rem; font-weight: 500; color: rgba(255,255,255,0.9);
            margin: 0.5rem 0 0 0; padding: 0;
            text-shadow: 0 1px 10px rgba(180, 41, 249, 0.3);
            text-align: left;
        }

        h1, h2, h3, h4, h5, h6, label, .stMarkdown, .stText {
            color: #e0e0e0 !important;
        }
        h3 { font-size: 22px !important; }
        .click-message {
            font-size: 16px !important; color: #26C5F3 !important;
            font-weight: 400 !important;
        }

        .stButton > button:not([kind="primary"]) {
            background-color: #a8f368 !important;
            color: #1a0a2e !important;
            border: none !important; border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-size: 1rem !important; font-weight: 600 !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
            cursor: pointer !important;
            text-align: center !important;
            justify-content: center !important;
            align-items: center !important;
            display: flex !important;
            height: 38px !important; line-height: 1.2 !important;
        }
        .stButton > button:not([kind="primary"]):hover {
            background-color: #8fd154 !important;
            color: #1a0a2e !important;
            border: none !important;
            box-shadow: 0 2px 15px rgba(168, 243, 104, 0.4) !important;
            transform: translateY(-1px) !important;
        }
        .stButton { display: block !important; width: 100% !important; }

        .stButton > button[kind="primary"] {
            background-color: #696eff !important;
            color: white !important;
            border: none !important; border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-size: 1rem !important; font-weight: 600 !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
            cursor: pointer !important;
            text-align: center !important;
            justify-content: center !important;
            align-items: center !important;
            display: flex !important;
            height: 38px !important; line-height: 1.2 !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #4f54d4 !important;
            color: white !important;
            box-shadow: 0 2px 15px rgba(105, 110, 255, 0.5) !important;
            transform: translateY(-1px) !important;
        }

        .stDownloadButton { display: none !important; }

        .stats-section h3 { margin-bottom: 1px !important; }
        .time-series-section h3 {
            margin-top: 25px !important; margin-bottom: 10px !important;
        }
        .regional-summary-section h3 {
            margin-top: 25px !important; margin-bottom: 10px !important;
        }

        .stSelectbox > div > div {
            background-color: #a8f368 !important;
            color: #1a0a2e !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            min-height: 38px !important; height: 38px !important;
            display: flex !important; align-items: center !important;
            font-size: 1rem !important; font-weight: 600 !important;
        }
        .stSelectbox > div > div:hover { background-color: #8fd154 !important; }
        .stSelectbox > div > div > div { color: #1a0a2e !important; }
        .stSelectbox svg { fill: #1a0a2e !important; color: #1a0a2e !important; }
        .stSelectbox > div > div ul { background-color: #1a0a2e !important; }
        .stSelectbox > div > div ul li { color: white !important; }
        .stSelectbox > div > div ul li:hover {
            background-color: #a8f368 !important; color: #1a0a2e !important;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #1a0a2e, #2d1b4e) !important;
            padding: 10px !important; border-radius: 8px !important;
            border: 1px solid rgba(180, 41, 249, 0.2) !important;
        }
        div[data-testid="stMetric"] label { color: #26C5F3 !important; }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #e0e0e0 !important;
        }

        .stAlert {
            background: linear-gradient(135deg, #1a0a2e, #2d1b4e) !important;
            color: #e0e0e0 !important;
        }
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #1a0a2e, #2d1b4e) !important;
            color: #e0e0e0 !important;
        }
        .streamlit-expanderContent {
            background: linear-gradient(135deg, #1a0a2e, #2d1b4e) !important;
            color: #e0e0e0 !important;
        }

        .leaflet-control-attribution { display: none !important; }
        .folium-map .leaflet-control-attribution { display: none !important; }
        .stDataFrame { background-color: #1a0a2e !important; }
        .stSidebar { background-color: #0e1117 !important; }
        hr { border-color: rgba(180, 41, 249, 0.3) !important; }
        .stCaption { color: #9ca3af !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---- TOP BAR: language + country ----
    configs = load_country_configs()

    if not configs:
        st.error(
            "No country configuration was found.\n\n"
            "The app expects at least one country JSON file (with a `key` and an "
            "`asset_path`) inside a **`config/`** folder next to `streamlit_app.py`.\n\n"
            "On GitHub: open your config file, click the ✏️ edit pencil, and rename it "
            "to `config/yourcountry.json` (typing `config/` before the name creates the "
            "folder). Then commit — the app will redeploy automatically."
        )
        st.stop()

    country_keys = list(configs.keys())
    if len(country_keys) == 1:
        selected_country = country_keys[0]
    else:
        try:
            default_key = st.query_params.get("country", country_keys[0])
        except AttributeError:
            default_key = st.experimental_get_query_params().get("country", [country_keys[0]])[0]
        if default_key not in configs:
            default_key = country_keys[0]
        selected_country = st.selectbox(
            t("country"),
            options=country_keys,
            index=country_keys.index(default_key),
            format_func=lambda k: country_label(configs[k]),
            label_visibility="collapsed",
        )
    cfg = configs[selected_country]

    dir_attr = "rtl" if st.session_state.lang in ["ar", "ku"] else "ltr"

    st.markdown(
        f"""
        <div class="banner">
            <div class="banner-inner">
                <div class="banner-title">
                    <h1>🌊 {t('dashboard_header')}</h1>
                    <div class="subtitle">{cfg.get('name_en', '')} | {datetime.now().strftime('%Y')}</div>
                    <div class="welcome">{t('welcome_subtitle')}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    lang_col1, lang_col2, lang_col3 = st.columns([4, 1, 1])
    with lang_col3:
        lang_options = {"English": "en", "العربية": "ar", "کوردی": "ku"}
        current_label = next(k for k, v in lang_options.items() if v == st.session_state.lang)
        selected_label = st.selectbox(
            "🌐",
            options=list(lang_options.keys()),
            index=list(lang_options.keys()).index(current_label),
            key="lang_selector_banner",
            label_visibility="collapsed",
        )
        if lang_options[selected_label] != st.session_state.lang:
            st.session_state.lang = lang_options[selected_label]
            st.rerun()

    st.markdown("---")
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1.2, 1.2, 1.2, 1.5, 1.5])

    with nav_col1:
        if st.button(t("nav_abstraction_mm"), key="nav_mm", use_container_width=True):
            st.session_state.selected_parameter = "abstraction_mm"
            st.session_state.map_generated = False
            st.session_state.regional_summary_data = None
            st.rerun()

    with nav_col2:
        if st.button(t("nav_abstraction_m3"), key="nav_m3", use_container_width=True):
            st.session_state.selected_parameter = "abstraction_m3"
            st.session_state.map_generated = False
            st.session_state.regional_summary_data = None
            st.rerun()

    with nav_col3:
        if st.button(t("nav_recharge"), key="nav_recharge", use_container_width=True):
            st.session_state.selected_parameter = "recharge"
            st.session_state.map_generated = False
            st.session_state.regional_summary_data = None
            st.rerun()

    with nav_col4:
        try:
            asset_path = cfg["asset_path"]
            assets = get_ee_assets(asset_path)
            if assets:
                asset_dates = [d for d in (parse_asset_date(a) for a in assets) if d is not None]
                if asset_dates:
                    min_date, max_date = min(asset_dates), max(asset_dates)
                    months = pd.date_range(start=min_date, end=max_date, freq="MS")
                    date_options = [date.strftime("%Y-%m") for date in months]

                    selected_date_str = st.selectbox(
                        t("select_date"),
                        options=date_options,
                        index=len(date_options) - 1,
                        key="top_date_selector",
                        label_visibility="collapsed",
                    )
                    st.session_state.selected_date_str = selected_date_str
        except Exception as e:
            st.warning("Could not load dates")

    with nav_col5:
        if st.button("🚀 " + t("generate_analysis"), key="top_generate", use_container_width=True, type="primary"):
            st.session_state.map_generated = True
            st.session_state.current_parameter = st.session_state.selected_parameter
            st.session_state.current_date = st.session_state.selected_date_str
            st.session_state.regional_summary_data = None
            st.rerun()

    st.markdown("---")

    defaults = {
        "last_clicked": None,
        "map_generated": False,
        "current_parameter": "abstraction_mm",
        "current_date": None,
        "time_series_data": None,
        "current_country": selected_country,
        "regional_summary_data": None,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

    if st.session_state.current_country != selected_country:
        st.session_state.current_country = selected_country
        st.session_state.map_generated = False
        st.session_state.last_clicked = None
        st.session_state.time_series_data = None
        st.session_state.regional_summary_data = None

    if st.session_state.selected_date_str is None:
        try:
            asset_path = cfg["asset_path"]
            assets = get_ee_assets(asset_path)
            if assets:
                asset_dates = [d for d in (parse_asset_date(a) for a in assets) if d is not None]
                if asset_dates:
                    latest_date = max(asset_dates)
                    st.session_state.selected_date_str = latest_date.strftime("%Y-%m")
        except:
            pass

    with st.container():
        if not st.session_state.map_generated:
            st.markdown(f"### 📊 {t('statistics')}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(t('minimum'), "—")
            with col2:
                st.metric(t('maximum'), "—")
            with col3:
                st.metric(t('mean'), "—")
        else:
            try:
                map_col, stats_col = st.columns([1, 1])

                with map_col:
                    st.markdown(f"### 🗺️ {t('interactive_map')}")

                    selected_date = datetime.strptime(st.session_state.current_date, "%Y-%m")
                    selected_year_month = selected_date.strftime("%Y_%m")

                    selected_asset = next(
                        (
                            a
                            for a in assets
                            if st.session_state.current_parameter in a and selected_year_month in a
                        ),
                        None,
                    )
                    if not selected_asset:
                        st.error(t("no_data_month"))
                        st.stop()

                    center_lat = float(cfg["center_lat"])
                    center_lon = float(cfg["center_lon"])
                    zoom = int(cfg["zoom"])

                    m = create_base_map(center_lat, center_lon, zoom)
                    ee_image = ee.Image(selected_asset)

                    opacity = st.session_state.get("opacity", 0.7)
                    vis_params = get_vis_params(st.session_state.current_parameter, selected_asset)
                    vis_params["opacity"] = opacity

                    add_ee_layer(
                        m,
                        ee_image,
                        vis_params,
                        f"{t(st.session_state.current_parameter)} {t('layer')}",
                    )
                    add_colormap(m, vis_params, st.session_state.current_parameter)
                    folium.LayerControl().add_to(m)

                    map_data = st_folium(m, width=None, height=850, returned_objects=["last_clicked"])

                    if map_data["last_clicked"] and map_data["last_clicked"] != st.session_state.last_clicked:
                        st.session_state.last_clicked = map_data["last_clicked"]
                        st.session_state.time_series_data = get_time_series_data(
                            point=[map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]],
                            parameter=st.session_state.current_parameter,
                            assets=tuple(assets),
                        )

                with stats_col:
                    st.markdown(f'<div class="stats-section"><h3>📊 {t("statistics")}</h3></div>', unsafe_allow_html=True)
                    try:
                        stats = ee_image.reduceRegion(
                            reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), None, True),
                            geometry=ee_image.geometry(),
                            scale=1000,
                            maxPixels=1e9,
                        ).getInfo()
                        prefix = next(
                            (k[: -len("_mean")] for k in stats if k.endswith("_mean")), "b1"
                        )

                        min_val = stats.get(f"{prefix}_min")
                        max_val = stats.get(f"{prefix}_max")
                        mean_val = stats.get(f"{prefix}_mean")

                        stat_cols = st.columns(3)
                        with stat_cols[0]:
                            st.metric(
                                t('minimum'),
                                f"{min_val:.2f}" if isinstance(min_val, (int, float)) else "N/A",
                            )
                        with stat_cols[1]:
                            st.metric(
                                t('maximum'),
                                f"{max_val:.2f}" if isinstance(max_val, (int, float)) else "N/A",
                            )
                        with stat_cols[2]:
                            st.metric(
                                t('mean'),
                                f"{mean_val:.2f}" if isinstance(mean_val, (int, float)) else "N/A",
                            )
                    except Exception as e:
                        st.error(f"{t('error_statistics')}: {str(e)}")

                    st.markdown(f'<div class="time-series-section"><h3>📈 {t("time_series_analysis")} <span class="click-message">({t("click_map")})</span></h3></div>', unsafe_allow_html=True)

                    center_lat = float(cfg["center_lat"])
                    center_lon = float(cfg["center_lon"])

                    if st.session_state.time_series_data:
                        clicked_lat = st.session_state.last_clicked["lat"]
                        clicked_lng = st.session_state.last_clicked["lng"]

                        csv_data = to_csv_bytes(st.session_state.time_series_data)
                        filename = f"{cfg['key']}_{st.session_state.current_parameter}_timeseries_{clicked_lat:.4f}_{clicked_lng:.4f}.csv"

                        fig = create_time_series_plot(
                            st.session_state.time_series_data,
                            st.session_state.current_parameter,
                            clicked_lat,
                            clicked_lng,
                            csv_data=csv_data,
                            filename=filename,
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        with st.expander(t("raw_data")):
                            st.dataframe(pd.DataFrame(st.session_state.time_series_data))
                    else:
                        fig = create_empty_time_series_plot(
                            st.session_state.current_parameter,
                            center_lat,
                            center_lon
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    st.markdown(f'<div class="regional-summary-section"><h3>📊 {t("regional_summary")}</h3></div>', unsafe_allow_html=True)

                    if st.session_state.regional_summary_data is None:
                        with st.spinner(t("computing")):
                            summary = get_regional_summary(
                                st.session_state.current_parameter,
                                tuple(assets),
                                int(cfg.get("native_scale_m", 20)),
                            )
                            if summary:
                                st.session_state.regional_summary_data = summary

                    if st.session_state.regional_summary_data:
                        summary = st.session_state.regional_summary_data
                        csv_data = to_csv_bytes(summary, value_col="mean")
                        filename = f"{cfg['key']}_{st.session_state.current_parameter}_regional_summary.csv"

                        fig = create_regional_summary_plot(
                            summary,
                            st.session_state.current_parameter,
                            csv_data=csv_data,
                            filename=filename,
                            button_text="📥 Download as CSV",
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        with st.expander(t("raw_data")):
                            st.dataframe(pd.DataFrame(summary))

            except Exception as e:
                st.error(f"{t('error_map')}: {str(e)}")
                st.error(traceback.format_exc())

    with st.expander(t("about_tool")):
        st.markdown(t("about_text"))


if __name__ == "__main__":
    main()
