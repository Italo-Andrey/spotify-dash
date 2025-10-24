import pandas as pd
import plotly.express as px

def process_recent_tracks(recent_data):
    # Converte dados em DataFrame
    data = []
    for item in recent_data:
        track = item['track']
        played_at = item['played_at']
        data.append({
            'Músicas': track['name'],
            'Artistas': track['artists'][0]['name'],
            'played_at': played_at
        })

    df = pd.DataFrame(data)
    
    # Converte played_at para datetime
    df['played_at'] = pd.to_datetime(df['played_at'], format='mixed', utc=True)
    
    # Ordena pelo played_at
    df = df.sort_values(by='played_at', ascending=True)
    
    return df



def generate_top_artists(df):
    top_artists = df['Artistas'].value_counts().head(5).reset_index()
    top_artists.columns = ['Artistas', 'count']
    
    fig = px.bar(
        top_artists,
        x='Artistas',
        y='count',
        labels={'count': 'Quantidade de músicas'},
        color='Artistas'
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
    )
    return fig.to_html(full_html=False)



def generate_top_tracks(df):
    top_tracks = df['Músicas'].value_counts().head(10).reset_index()
    top_tracks.columns = ['Músicas', 'count']
    
    fig = px.bar(
        top_tracks,
        x='Músicas',
        y='count',
        labels={'count': 'Quantidade de vezes tocada'},
        color='Músicas'
    )
    return fig.to_html(full_html=False)
