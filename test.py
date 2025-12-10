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
def presenceWinratefig():
    bins = [0, 3, 4, 5, float("inf")]
    labels = ["< 3", "3-4", "4-5", "> 5"]
    df["KDA_band"] = pd.cut(df["KDA_num"], bins=bins, labels=labels, right=False)

    fig = px.scatter(
        df,
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
            "CSD@15": True,
            "GD@15": True,
            "XPD@15": True,
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
    
    least = df.loc[df["Picks"].loc[df["Picks"] >= 1].idxmin()]
    most  = df.loc[df["Picks"].idxmax()]
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


    return fig

def earlyGameFig():
    metrics = ["GD@15", "XPD@15", "CSD@15"]
    titles = ["Gold difference at 15 minutes", "XP difference at 15 minutes", "CS difference at 15 minutes"]

    fig = make_subplots(
        rows=1, cols=3,
        shared_yaxes=True,
        subplot_titles=titles
    )

    for i, col_name in enumerate(metrics, start=1):
        fig.add_trace(
            go.Scatter(
                x=df[col_name],
                y=df["WinRate_num"],
                mode="markers",
                marker=dict(
                    size=df["Picks"],
                    color=df["KDA_num"],   # or use your KDA_band mapping
                    colorscale="Viridis",
                    showscale=(i == 3)    # show colorbar once if you want
                ),
                text=df["Champion"],
                hovertemplate=(
                    "Champion=%{text}<br>"
                    f"{col_name}=%{{x}}<br>"
                    "Winrate=%{y}<br>"
                    "Picks=%{marker.size}"
                )
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
            ]
        ),
        dcc.Graph(
            id="presence-winrate-graph",
            figure=presenceWinratefig(),
            style={"width": "100%", "flex": "0 0 60%"}  # ~60% of height
        ),
        dcc.Graph(
            id="early-game-graph",
            figure=earlyGameFig(),
            style={"width": "100%", "flex": "0 0 40%"}  # ~40% of height
        ),
    ],
)


@app.callback(
    Output("presence-winrate-graph", "figure"),
    Output("early-game-graph", "figure"),
    Input("champion-search", "value"),
)
def update_figures(search_value):
    print("=== Champion Searched ===")
    print("Raw search_value:", repr(search_value))
    # 1) Decide which champions are "selected"
    if search_value:
        matches = df.loc[df["Champion"].str.lower() == search_value.lower()]
        if matches.empty:
            print("No champion matched query:", search_value)
        else:
            matched_champion = matches.iloc[0]
            print("Found:",  matched_champion["Champion"])
    else:
        print("Empty search, selecting all champions")


    # Always return two figures for the two Outputs
    fig_main = presenceWinratefig()
    fig_early = earlyGameFig()
    return fig_main, fig_early

if __name__ == "__main__":
    app.run(debug=True)