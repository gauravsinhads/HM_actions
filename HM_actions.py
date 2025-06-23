elif st.session_state.page == "HM actions":
    st.title("HM actions")

    # Load data
    @st.cache_data
    def load_data(): return session.sql("""select * from STREAMLITAPPS.talkpush.Folder_Logs""").toPandas()
    df = load_data()


    today = datetime.today()
    df["DATE_DAY"] = pd.to_datetime(df["DATE_DAY"])
    custom_colors = ["#2F76B9",	"#3B9790", "#F5BA2E", "#6A4C93", "#F77F00", "#B4BBBE","#e6657b", "#026df5","#5aede2"]

    col = st.columns(2)
      # Ensure valid dates before showing date filter
    if df['DATE_DAY'].dropna().empty:
        st.error("No valid DATE_DAY values available in the data.")
        st.stop()

    min_date = df['DATE_DAY'].min()
    max_date = df['DATE_DAY'].max()

    default_start_date = max_date - pd.Timedelta(days=60)
    with col[1]: start_date, end_date = st.date_input("Select Date Range",[default_start_date, max_date])

    # Filter data based on selections
    df1 = df[
        (df['DATE_DAY'] >= pd.to_datetime(start_date)) &
        (df['DATE_DAY'] <= pd.to_datetime(end_date))]

    # bar dropdown
    col = st.columns(3)


    # Column 1 - Campaign Title expander
    with col[0]:
            selected_campaigns = st.multiselect(
                    "Campaign Title", options=sorted(df['CAMPAIGNTITLE'].dropna().unique()), default=None )

    #Column 2 - Work Location expander
    with col[1]:
        selected_worklocations = st.multiselect("Site", options=sorted(df['CAMPAIGN_SITE'].dropna().unique()), default=None )

    # Column 3 - Time Period selectbox
    with col[2]:
        aggregation_option = st.selectbox("Aggregation Level", ["Monthly (12 max)", "Weekly (12 max)", "daily (30 max)"])

    if selected_campaigns: df1 = df1[df1['CAMPAIGNTITLE'].isin(selected_campaigns)]

    if selected_worklocations: df1 = df1[df1['CAMPAIGN_SITE'].isin(selected_worklocations)]




    # Get the latest date from your data
    latest_date = df1["DATE_DAY"].max()

    # Apply Aggregation based on Selection
    if aggregation_option == "Monthly (12 max)":
        start_date = latest_date - timedelta(days=365)
        df1 = df1[df1["DATE_DAY"] >= start_date]
        df1["DATE_GROUP"] = df1["DATE_DAY"].dt.to_period('M').dt.to_timestamp()  # Format as Feb-2024
        #df["DATE_GROUP"] = df["DATE_DAY"].dt.to_period("M").astype(str)  # Format as Feb-2024
    elif  aggregation_option == "Weekly (12 max)":
        df1["DATE_GROUP"] = df1["DATE_DAY"] + pd.to_timedelta(6 - df1["DATE_DAY"].dt.weekday, unit="D")
    else:
        df1["DATE_GROUP"] = pd.to_datetime(df1["DATE_DAY"], format='%b-%d-%Y')
    # Apply Aggregation based on Selection2
    if aggregation_option == "daily (30 max)":
        df1 = df1[df1["DATE_DAY"] >= latest_date - pd.Timedelta(days=30)]
    elif  aggregation_option == "Weekly (12 max)":
        df1 = df1[df1["DATE_DAY"] >= latest_date - pd.Timedelta(weeks=12)]
    else:
        df1["DATE_GROUP2"] = pd.to_datetime(df1["DATE_DAY"], format='%b-%d-%Y')



    df_f = df1[df1["MOVED_BY"] == "Manager" ]    

    #FIG1
        # Group by month,and weeky
    df_rej = df1.groupby(["DATE_GROUP"], as_index=False)[['REJECTED_BY_MANAGER', 'MOVED_BY_MANAGER']].sum()
        # Calculate rejection percentage
    df_rej['REJECT_PERCENT'] = (df_rej['REJECTED_BY_MANAGER'] / df_rej['MOVED_BY_MANAGER']) * 100
        #Create column with text type
    df_rej["TEXT_LABEL"] = df_rej["REJECT_PERCENT"].apply(lambda x: f"{x:.2f}%")
        # creation of the plot
    fig1 = px.line(df_rej, 
                   x="DATE_GROUP", y="REJECT_PERCENT",
                   markers=True,  # Add points (vertices)
                   title="Reject % Over the time",
                   labels={"DATE_GROUP": "Time", "REJECT_PERCENT": "Rejection %"},
                   line_shape="linear", text="TEXT_LABEL")  # Use formatted text
        # Update the trace to display the text on the chart
    fig1.update_traces( textposition="top center", fill='tozeroy' , fillcolor="rgba(0, 0, 255, 0.2)")

    st.plotly_chart(fig1, use_container_width=True)

    #FIG 2
        # Create a flag where FOLDER_TO_TITLE == "Talent Pool"
    df_f["IS_TALENT_POOL"] = df_f["FOLDER_TO_TITLE"].eq("Talent Pool").astype(int)
        # Group by DATE_GROUP and calculate total moves and Talent Pool moves
    df_pass = df_f.groupby("DATE_GROUP", as_index=False).agg(
        MOVED_BY_MANAGER=('MOVED_BY', 'count'),
        PASSED_TO_TALENT_POOL=('IS_TALENT_POOL', 'sum')   )
       # Calculate percentage
    df_pass["PASS_PERCENT"] = (df_pass["PASSED_TO_TALENT_POOL"] / df_pass["MOVED_BY_MANAGER"]) * 100
    df_pass["TEXT_LABEL"] = df_pass["PASS_PERCENT"].apply(lambda x: f"{x:.2f}%")
        # Create the chart
    fig2 = px.line(  df_pass,
        x="DATE_GROUP", y="PASS_PERCENT",
        markers=True,   title="Pass % Over Time",
        labels={"DATE_GROUP": "Time", "PASS_PERCENT": "Pass % (Talent Pool)"},
        line_shape="linear", text="TEXT_LABEL"    )
        # Format trace
    fig2.update_traces(       textposition="top center",
        fill='tozeroy',
        fillcolor="rgba(0, 128, 0, 0.2)"    )
        #  Show the chart
    st.plotly_chart(fig2, use_container_width=True)

    # ------------------- START: NEW CHART ADDED HERE -------------------

    # FIG 2.1: Pass to Talent Pool Percentage by CEFR Score
    # Group by DATE_GROUP and TALKSCORE_CEFR to get detailed stats
    df_cefr = df_f.groupby(["DATE_GROUP", "TALKSCORE_CEFR"], as_index=False).agg(
        MOVED_BY_MANAGER=('MOVED_BY', 'count'),
        PASSED_TO_TALENT_POOL=('IS_TALENT_POOL', 'sum')
    )
    
    # Calculate pass percentage for each CEFR group
    df_cefr["PASS_PERCENT"] = (df_cefr["PASSED_TO_TALENT_POOL"] / df_cefr["MOVED_BY_MANAGER"]) * 100
    
    # Define the specific order for the CEFR categories
    cefr_category_order = ["C1", "C2", "B1", "B1+", "B2", "B2+", "A0", "A2", "A2+"]

    # Create the multi-line chart
    fig_cefr = px.line(
        df_cefr,
        x="DATE_GROUP",
        y="PASS_PERCENT",
        color="TALKSCORE_CEFR",  # Use TALKSCORE_CEFR to create multiple lines
        markers=True,
        title="Pass % to Talent Pool by CEFR Score Over Time",
        labels={"DATE_GROUP": "Time", "PASS_PERCENT": "Pass % (Talent Pool)", "TALKSCORE_CEFR": "CEFR Score"},
        line_shape="linear",
        category_orders={"TALKSCORE_CEFR": cefr_category_order}  # Apply the custom sort order
    )

    # Show the new chart
    st.plotly_chart(fig_cefr, use_container_width=True)

    # -------------------- END: NEW CHART ADDED HERE --------------------


    #FIG 3 
    
    #FIG 3# Normalize the counts per month to percentages
    df3_actions = df_f.groupby(["DATE_GROUP", "FOLDER_TO_TITLE"]).size().reset_index(name="COUNT")
    # Normalize to get percentage per month
    df3_actions["PERCENTAGE"] = df3_actions.groupby("DATE_GROUP")["COUNT"].transform(lambda x: x / x.sum())
    df3_actions["TEXT_LABEL"] = df3_actions["PERCENTAGE"].apply(lambda x: f"{x * 100:.2f}%")
    #create chart
    fig3 = px.bar(       df3_actions,
        x="DATE_GROUP", y="PERCENTAGE",
        color="FOLDER_TO_TITLE",
        text="TEXT_LABEL",  # <- Use the corrected label
        title="Percentage of actions BY Manager",
        labels={ "DATE_GROUP": "Time",
            "PERCENTAGE": "Percentage",
            "FOLDER_TO_TITLE": "Actions" }    )
    fig3.update_layout(barmode="stack", yaxis=dict(tickformat=".0%"), height=500)

    st.plotly_chart(fig3, use_container_width=True)
    

    #TABLE
    # Step 1: Clean the MOVER_EMAIL column
    def clean_email(email):
        if pd.isna(email) or not isinstance(email, str):
            return email  # Return as-is if it's NaN or not a string
        return re.sub(r'\+.*?@', '@', email)  # Remove everything between + and @

    # Convert MOVER_EMAIL to string type first (NaN will become 'nan')
    df1['CLEANED_MOVER_EMAIL'] = df1['MOVER_EMAIL'].astype(str).apply(clean_email)

    # Replace 'nan' with actual NaN if needed
    df1['CLEANED_MOVER_EMAIL'] = df1['CLEANED_MOVER_EMAIL'].replace('nan', np.nan)

    # Step 2: Group by cleaned MOVER_EMAIL (filter out NaN values if needed)
    df_mover = df1.groupby('CLEANED_MOVER_EMAIL')[['REJECTED_BY_MANAGER', 'MOVED_BY_MANAGER']].sum()

    # Step 3: Calculate rejection percentage
    df_mover['REJECT_PERCENT'] = (df_mover['REJECTED_BY_MANAGER'] / df_mover['MOVED_BY_MANAGER']) * 100
    df_mover["REJECT %"] = df_mover["REJECT_PERCENT"].apply(lambda x: f"{x:.2f}%")
    df_mover = df_mover.sort_values(by='REJECTED_BY_MANAGER', ascending=False)
    df_mover = df_mover.reset_index()
    df_mover = df_mover.drop(columns=['REJECT_PERCENT'])
    # Step 4: Count how many candidates each manager moved to 'Talent Pool'
    df_talent = df1[df1['FOLDER_TO_TITLE'] == "Talent Pool"]
    df_talent_grouped = df_talent.groupby('CLEANED_MOVER_EMAIL').size().reset_index(name='PASSED')

    # Step 5: Merge with the main df_mover
    df_mover = df_mover.merge(df_talent_grouped, on='CLEANED_MOVER_EMAIL', how='left')

    # Step 6: Fill missing values with 0 (managers with no 'Talent Pool' moves)
    df_mover['PASSED'] = df_mover['PASSED'].fillna(0).astype(int)

    # Step 7: Calculate PASS %
    df_mover['PASS_PERCENT'] = (df_mover['PASSED'] / df_mover['MOVED_BY_MANAGER']) * 100
    df_mover['PASS %'] = df_mover['PASS_PERCENT'].apply(lambda x: f"{x:.2f}%")

    # Step 8: Drop helper columns if needed
    df_mover = df_mover.drop(columns=['PASS_PERCENT'])

    # Show the table
    st.subheader("Reject % & Pass % By HM")
    st.dataframe(df_mover, use_container_width=True)
