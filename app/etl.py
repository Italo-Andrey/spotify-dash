import pandas as pd
import plotly.express as px

def process_recent_tracks(recent_data):
    # Converte dados em DataFrame
    data = []
    for item in recent_data:
        track = item['track']
        played_at = item['played_at']
        data.append({
            'music': track['name'],
            'artist': track['artists'][0]['name'],
            'played_at': played_at
        })

    df = pd.DataFrame(data)
    df['played_at'] = pd.to_datetime(df['played_at'], format='mixed', utc=True)
    return df

def generate_top_artists(df):
    top_artists = df['artist'].value_counts().head(5).reset_index()
    top_artists.columns = ['artist', 'count']
    
    fig = px.bar(
        top_artists,
        x='artist',
        y='count',
        title='Top 5 Artistas Recentes',
        labels={'count': 'Quantidade de músicas'},
        color='artist'
    )

    # Retorna o HTML do gráfico para embutir no template
    return fig.to_html(full_html=False)

def generate_hourly_distribution(df):
    df['hour'] = df['played_at'].dt.hour
    hourly_counts = df['hour'].value_counts().sort_index()

    fig = px.bar(
        x=hourly_counts.index,
        y=hourly_counts.values,
        labels={'x': 'Hora do dia', 'y': 'Quantidade de músicas'},
        title='Distribuição de músicas por hora do dia'
    )
    return fig.to_html(full_html=False)

def generate_top_tracks(df):
    top_tracks = df['music'].value_counts().head(10).reset_index()
    top_tracks.columns = ['music', 'count']
    
    fig = px.bar(
        top_tracks,
        x='music',
        y='count',
        title='Top 10 Músicas Recentes',
        labels={'count': 'Quantidade de vezes tocada'},
        color='music'
    )
    return fig.to_html(full_html=False)
