import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
from dash import Dash, dcc, html
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

df = pd.read_csv("champions.csv")
df = df[(df["Picks"] > 0) | (df["Bans"] > 0)]

df["Presence_num"] = df["Presence"].str.rstrip('%').astype(float)
df["WinRate_num"]  = df["Winrate"].str.rstrip('%').astype(float)
df["KDA_num"] = pd.to_numeric(df["KDA"], errors="coerce")
allowed_slider_values = [1, 5, 10, 15, 20]
average_GT = "33:03:00"
app = Dash(__name__)

# create empty 2x2 grid
grid = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Presence vs Win rate",
        "Plot 2 title",
        "Plot 3 title",
        "Plot 4 title",
    )
)
def presenceWinratefig(min_picks, selected_champion=None):
    filtered_picks = df[df["Picks"] >= min_picks]   # keep only champs with >=5 games
    bins = [0, 3, 4, 5, float("inf")]
    labels = ["< 3", "3-4", "4-5", "> 5"]
    filtered_picks["KDA_band"] = pd.cut(filtered_picks["KDA_num"], bins=bins, labels=labels, right=False)

    fig = px.scatter(
        filtered_picks,
        x="Presence_num",
        y="WinRate_num",
        size="Picks",
        color="KDA_band",
        color_discrete_map={
        "< 3": "gray",
        "3-4": "green",
        "4-5": "blue",
        "> 5": "orange",
        },
        hover_name="Champion",
        hover_data={
            "Presence_num": False,
            "WinRate_num": False,
            "KDA_band": False,
            "Picks": True,
            "Bans": True,
            "Winrate": True,
            "KDA": True,
            "DPM": True,
            "GT": True,
            "CSD@15": False,
            "GD@15": False,
            "XPD@15": False,
        },
    )

    # base layout + extra right margin
    fig.update_layout(
        xaxis_title="Presence",
        yaxis_title="Win rate",
        title="Presence vs Win Rate by Champion",
        showlegend=True,
        xaxis_range=[0, 100],   # stop at 100%
        yaxis_range=[0, 100],   # stop at 100%
        margin=dict(l=60, r=180, t=60, b=60),
    )

    # quadrant lines and labels
    fig.add_hline(y=50, line_dash="dash", line_color="black")
    fig.add_vline(x=50, line_dash="dash", line_color="black")

    fig.add_annotation(x=25, y=75, text="Undervalued strong picks",
                    showarrow=False, font=dict(size=16, color="rgba(0,0,0,0.25)"))
    fig.add_annotation(x=75, y=75, text="Meta power picks",
                    showarrow=False, font=dict(size=16, color="rgba(0,0,0,0.25)"))
    fig.add_annotation(x=25, y=25, text="Weak / niche picks",
                    showarrow=False, font=dict(size=16, color="rgba(0,0,0,0.25)"))
    fig.add_annotation(x=75, y=25, text="Overprioritized / overrated",
                    showarrow=False, font=dict(size=16, color="rgba(0,0,0,0.25)"))
    
    least = filtered_picks.loc[filtered_picks["Picks"].loc[filtered_picks["Picks"] >= 1].idxmin()]
    most  = filtered_picks.loc[filtered_picks["Picks"].idxmax()]
    # least picked
    fig.add_annotation(
        x=least["Presence_num"],
        y=least["WinRate_num"],
        text=f"Least picked ({least['Champion']}, {least['Picks']} picks)",
        showarrow=True,
        arrowhead=2,
        ax=40, ay=40,       # move label away from point
    )

    # most picked
    fig.add_annotation(
        x=most["Presence_num"],
        y=most["WinRate_num"],
        text=f"Most picked ({most['Champion']}, {most['Picks']} picks)",
        showarrow=True,
        arrowhead=2,
        ax=-40, ay=-40,
    )

    if selected_champion is not None:
        fig.add_annotation(
            x=selected_champion["Presence_num"],
            y=selected_champion["WinRate_num"],
            text=f"Selected: {selected_champion['Champion']}",
            showarrow=True,
            arrowhead=2,
            ax=0, ay=-50,
            font=dict(color="red", size=14),
            arrowcolor="red",
        )
    return fig

def earlyGameFig(min_picks, selected_champion=None):
    metrics = ["GD@15", "XPD@15", "CSD@15"]
    titles = ["Gold difference at 15 minutes", "XP difference at 15 minutes", "CS difference at 15 minutes"]
    filtered_picks = df[df["Picks"] >= min_picks]   # keep only champs with >=5 games
    fig = make_subplots(
        rows=1, cols=3,
        shared_yaxes=True,
        subplot_titles=titles
    )

    for i, col_name in enumerate(metrics, start=1):
        fig.add_trace(
            go.Scatter(
                x=filtered_picks[col_name],
                y=filtered_picks["WinRate_num"],
                mode="markers",
                text=filtered_picks["Champion"],
                showlegend=False,
                hovertemplate="%{text}<br>%{x}, %{y}<extra></extra>"
            ),
            row=1, col=i
        )

    fig.update_yaxes(title_text="Win rate", row=1, col=1)
    fig.update_xaxes(title_text="GD@15", row=1, col=1)
    fig.update_xaxes(title_text="XPD@15", row=1, col=2)
    fig.update_xaxes(title_text="CSD@15", row=1, col=3)

    fig.update_layout(
        margin=dict(l=60, r=40, t=40, b=40)
    )
    
    # highlight: single extra point per subplot
    if selected_champion is not None:
        for i, col_name in enumerate(metrics, start=1):
            fig.add_trace(
                go.Scatter(
                    x=[selected_champion[col_name]],
                    y=[selected_champion["WinRate_num"]],
                    mode="markers",
                    marker=dict(
                        size=18,
                        color="steelblue",                 # same fill
                        line=dict(width=4, color="deepskyblue"),  # bright outline
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                ),
                row=1, col=i,
            )
    return fig

def topNBarchart(metric= "DPM", n=10, min_picks=1):
    filtered_picks = df[df["Picks"] >= min_picks]   # keep only champs with >=5 games

    df_metric = filtered_picks.sort_values(by=metric, ascending=False).head(n)
    metric_labels = {
        "DPM": "Damage per Minute",
        "GD@15": "Gold difference @ 15",
        "XPD@15": "XP difference @ 15",
        "CSD@15": "CS difference @ 15",
        "WinRate_num": "Win rate",
    }
    x_title = metric_labels.get(metric, metric)


    fig = go.Figure(
        data=[
            go.Bar(
                x=df_metric[metric],
                y=df_metric["Champion"],
                orientation="h",
            )
        ]
    )

    fig.update_layout(
        xaxis_title=x_title,
        yaxis=dict(autorange="reversed"),
        title=f"Top {n} champions by {x_title}",
        margin=dict(l=120, r=40, t=40, b=40),
    )

    return fig
app.layout = html.Div(
    style={
        "height": "100vh",      # fill full browser height
        "display": "flex",
        "flexDirection": "column",
    },
    children=[
        html.Div(
            children= [
                html.Label("Search champion: "),
                dcc.Input(id="champion-search", type="text", value="", debounce=True),
                html.Label("Min games: "),
                dcc.Slider(
                    id="min-picks-slider",
                    min=0,
                    max=len(allowed_slider_values) - 1,
                    step=None,
                    value=0,
                    marks={i: str(v) for i, v in enumerate(allowed_slider_values)},
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
            ]
        ),
        dcc.Graph(
            id="presence-winrate-graph",
            figure=presenceWinratefig(min_picks=1),
            style={"width": "100%", "flex": "0 0 50%"}  # ~5ö% of height
        ),
        html.Div(
            style={
                "display": "flex",
                "flex": "1 1 40%",
            },
            children=[
                dcc.Graph(
                    id="early-game-graph",
                    style={"width": "50%", "height": "100%"},
                ),
                html.Div(   # wrapper for dropdown + graph
                    style={
                        "width": "50%",
                        "height": "100%",
                        "display": "flex",
                        "flexDirection": "column",
                    },
                    children=[
                        dcc.Dropdown(
                            id="top-n-metric-dropdown",
                            options=[
                                {"label": "Damage per Minute", "value": "DPM"},
                                {"label": "Gold difference @ 15", "value": "GD@15"},
                                {"label": "XP difference @ 15", "value": "XPD@15"},
                                {"label": "CS difference @ 15", "value": "CSD@15"},
                                {"label": "Win rate", "value": "WinRate_num"},
                            ],
                            value="DPM",
                            clearable=False,
                            style={"marginBottom": "10px"},
                        ),
                        dcc.Graph(
                            id="top-n-graph",
                            style={"flex": "1 1 auto"},  # fill remaining space
                        ),
                    ], 
                ),
            ],
        ),
    ],
)


@app.callback(
    Output("presence-winrate-graph", "figure"),
    Output("early-game-graph", "figure"),
    Output("top-n-graph", "figure"),
    Input("champion-search", "value"),
    Input("top-n-metric-dropdown", "value"),  
    Input("min-picks-slider", "value"),

)
def update_figures(search_value, metric, min_picks_index):
    print("=== Champion Searched ===")
    print("Raw search_value:", repr(search_value))
    # 1) Decide which champions are "selected"
    df_filtered = df[df["Picks"] >= allowed_slider_values[min_picks_index]].copy()
    matched_champion = None
    if search_value:
        matches = df_filtered.loc[df_filtered["Champion"].str.lower() == search_value.lower()]
        if matches.empty:
            print("No champion matched query:", search_value)
        else:
            matched_champion = matches.iloc[0]
            print("Found:",  matched_champion["Champion"])
    else:
        print("Empty search, selecting all champions")


    # Always return two figures for the two Outputs
    fig_main = presenceWinratefig(allowed_slider_values[min_picks_index], matched_champion)
    fig_early = earlyGameFig(allowed_slider_values[min_picks_index], matched_champion)
    fig_topn = topNBarchart(metric=metric, n=10, min_picks=allowed_slider_values[min_picks_index])  # or any metric you want

    return fig_main, fig_early, fig_topn

if __name__ == "__main__":
    app.run(debug=True)