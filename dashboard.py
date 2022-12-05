import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.express as px

from dash import Dash, dcc, html, Input, Output
from calendar import monthrange

app = Dash(
    __name__,
    external_stylesheets=["assets/custom.css"]
)


def clean_dep(dep) -> str:
    dep = str(dep)
    if len(dep) == 1:
        return f"0{dep}"
    return dep


def clean_and_read_data() -> pd.DataFrame:
    raw_df = pd.read_csv("./FD_NAIS_2019.csv", delimiter=";")

    # A bit of cleaning, useful later.

    raw_df["DEPNAIS"] = raw_df["DEPNAIS"].replace({
        dep: clean_dep(dep)
        for dep in raw_df["DEPNAIS"].unique()
    })
    return raw_df


# Load primary dataset

df = clean_and_read_data()

gdf = gpd.read_file("https://france-geojson.gregoiredavid.fr/repo/departements.geojson")
gdf = gdf.set_index("code", drop=True)

# Per-graph dataframes

df_choropleth = pd.DataFrame(
    [
        (code, df[df["DEPNAIS"] == clean_dep(code)].shape[0])
        for code in gdf.index
    ],
    columns=["Department", "Births (abs)"],
)
df_choropleth["Births (log)"] = np.log(df_choropleth["Births (abs)"])

months = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
df_barplot = pd.DataFrame(
    [
        (month, months[month - 1], df[df["MNAIS"] == month].shape[0])
        for month in df["MNAIS"].unique()
    ],
    columns=["Month_ind", "Month (birth)", "Births (abs)"],
).sort_values("Month_ind")
df_barplot["Births (norm)"] = df_barplot.apply(
    lambda ser: round((ser["Births (abs)"] / monthrange(2019, ser["Month_ind"])[1] * 30)),
    axis=1,
)
df_barplot["Month (procreation)"] = df_barplot["Month (birth)"].replace({
    "January": "April 2018",
    "February": "May 2018",
    "March": "June 2018",
    "April": "July 2018",
    "May": "August 2018",
    "June": "September 2018",
    "July": "October 2018",
    "August": "November 2018",
    "September": "December 2018",
    "October": "January 2019",
    "November": "February 2019",
    "December": "March 2019",
})
df_barplot["Number"] = df_barplot["Births (norm)"]  # alias


# "Static" figures

def age_heatmap():
    df_heatmapage = pd.DataFrame(
        index=sorted(df["AGEXACTM"].unique(), reverse=True),
        columns=sorted(df["AGEXACTP"].unique()),
    ).fillna(0)
    for i, ser in df.groupby(["AGEXACTP", "AGEXACTM"])["ANAIS"].count().reset_index().iterrows():
        df_heatmapage[ser["AGEXACTP"]][ser["AGEXACTM"]] = ser["ANAIS"]

    fig = px.imshow(
        df_heatmapage,
        labels=dict(
            x="Father's age",
            y="Mother's age",
            color="Births",
        ),
        x=df_heatmapage.columns,
        y=df_heatmapage.index,
        title="Comparison of parent's age and the number of births",
    )
    fig.update_xaxes(side="top")
    return fig


def last_name_pie():
    ind_to_origine_nom = {
        1: "Father",
        2: "Mother",
        3: "Father - Mother",
        4: "Mother - Father",
        5: "Other",
    }

    df["Last name choice"] = df.apply(
        lambda ser: ind_to_origine_nom.get(ser["ORIGINOM"], "Father"),
        axis=1,
    )
    ind_to_nat = {
        1: "French",
        2: "Foreign",
    }

    groups = df.groupby(["INDNATP", "INDNATM", "Last name choice"]).count()[
        "ANAIS"].reset_index()

    fig = px.sunburst(
        pd.DataFrame(
            [
                (ser["ANAIS"],
                 f"{ind_to_nat[ser['INDNATP']]}/{ind_to_nat[ser['INDNATM']]}",
                 ser["Last name choice"])
                for i, ser in groups.iterrows()
            ],
            columns=("Births", "Parents nationality (father/mother)",
                     "Last name choice"),
        ),
        values='Births',
        path=['Parents nationality (father/mother)', 'Last name choice'],
        title="Representation of children born from French and/or foreign parents, and last name choice",
    )
    return fig


def last_name_line():
    data = []
    for age in sorted(df["AGEXACTP"].unique()):
        sub_df = df[(df["AGEXACTP"] == age) | (df["AGEXACTM"] == age)]
        for name_choice in df["Last name choice"].unique():
            data.append((
                age, name_choice,
                ((sub_df["Last name choice"] == name_choice).sum() /
                 sub_df.shape[0]) * 100
            ))

    fig = px.line(
        pd.DataFrame(
            data,
            columns=("Age", "Last name choice", "Usage (%)")
        ),
        range_y=(0, 100),
        x="Age", y="Usage (%)", color="Last name choice",
        title="Last name choice depending on parents' age",
    )
    return fig


def recognition():
    data = []
    for age in sorted(df["AGEXACTP"].unique()):
        data.append((
            "Mother", age,
            (((df["AGEXACTM"] == age) & (
                        (df["ARECM"] != 0) | (df["AMAR"] != 0))).sum() / (
                         df["AGEXACTM"] == age).sum()) * 100
        ))
        data.append((
            "Father", age,
            (((df["AGEXACTP"] == age) & (
                        (df["ARECP"] != 0) | (df["AMAR"] != 0))).sum() / (
                         df["AGEXACTP"] == age).sum()) * 100
        ))

    fig = px.line(
        pd.DataFrame(
            data,
            columns=("Parent", "Age", "Recognition rate (%)")
        ),
        range_y=(0, 100),
        x="Age", y="Recognition rate (%)", color="Parent",
        title="Recognition rate per parent depending on age",
    )
    return fig


# Layout

app.layout = html.Div([

    html.Div([
        html.H1(
            '2019 birth rates in France',
            style={'textAlign': 'center'}
        ),
    ], className="title"),

    html.Div([
        html.P("Can be found on Github!"),
    ], className="info"),

    html.Div([

        html.Div([
            html.H1("Parameters")
        ], className="params_title"),

        html.Div([
            html.H2("Graph scale:"),
            dcc.RadioItems(
                ['Absolute', 'Logarithmic'],
                'Absolute',
                id='choropleth-graph-scale'
            ),
        ], className="map_params"),

        html.Div([
            html.H2("Births:"),
            dcc.RadioItems(
                ['Absolute', 'Normalized'],
                'Absolute',
                id='barplot-graph-bars'
            ),
            html.H2("Months:"),
            dcc.RadioItems(
                ['Births', 'Procreations'],
                'Births',
                id='barplot-graph-type'
            ),
        ], className="months_params"),

    ], className="params"),

    html.Div([
        dcc.Graph(id="choropleth-graph"),
    ], className="map"),

    html.Div([
        dcc.Graph(id="barplot-graph"),
    ], className="months"),

    html.Div([
        dcc.Graph(figure=age_heatmap()),
    ], className="heatmap"),

    html.Div([
        dcc.Graph(figure=last_name_pie()),
    ], className="last_name_pie"),

    html.Div([
        dcc.Graph(figure=last_name_line()),
    ], className="last_name_line"),

    html.Div([
        dcc.Graph(figure=recognition()),
    ], className="recognition"),

], className="container")


@app.callback(
    Output("choropleth-graph", "figure"),
    Input("choropleth-graph-scale", "value"),
)
def update_map(scale: str):
    birth_var = {
        "Absolute": "Births (abs)",
        "Logarithmic": "Births (log)"
    }
    fig = px.choropleth_mapbox(
        df_choropleth,
        geojson=gdf.geometry,
        locations='Department',
        color=birth_var[scale],
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        zoom=4, center={"lat": 46.2447976, "lon": 4.1123575},
        opacity=0.5,
        title="Births per department",
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


@app.callback(
    Output("barplot-graph", "figure"),
    Input("barplot-graph-bars", "value"),
    Input("barplot-graph-type", "value"),
)
def update_barplot(bars: str, data_type: str):
    birth_var = {
        "Absolute": "Births (abs)",
        "Normalized": "Births (norm)",
    }
    type_var = {
        "Births": "Month (birth)",
        "Procreations": "Month (procreation)",
    }
    fig = px.bar(
        df_barplot,
        x=type_var[data_type], y=birth_var[bars],
        title=f"{data_type} per month",
    )
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
