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
    df['played_at'] = pd.to_datetime(df['played_at'])
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