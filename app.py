import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import urllib.request as request

# data proprocess
r = request.urlopen("https://raw.githubusercontent.com/founting/votes/master/votings.csv")
data=pd.read_csv(r)
topics=np.unique(data['topic'])
parties=np.array(data.columns[5:20])

tdist=[]
propose=[]
pvotes=[]
for i in range(data.shape[0]):
    #tdist
    t=data.loc[i]['topic']
    d=data.loc[i]['decision']
    if d==1:
        tdist.append([t,1,0])
    else:
        tdist.append([t,0,1])
    #propose
    proposer=data.loc[i]['proposer']
    propose.append([proposer,t,1])
    #pvotes
    for p in parties:
        v=data.iloc[i][p]
        if v==1:
            pvotes.append([p,t,'support',1])
        else:
            pvotes.append([p,t,'against',1])

for t in topics:
    pvotes.append([parties[0],t,'support',0])
    pvotes.append([parties[0],t,'against',0])

#topic distribution
tdist=pd.DataFrame(tdist,columns=['topic','aangenomen','verworpen'])
tdist=tdist.groupby('topic').sum().reset_index()

fig_td=go.Figure(
    data=[
        go.Bar(name='aangenomen', x=tdist['topic'], y=tdist['aangenomen'],base=0,marker_color='#87CE70'),
        go.Bar(name='verworpen', x=tdist['topic'], y=-tdist['verworpen'],base=0,marker_color='#FFCC80')
    ],
    layout=go.Layout(
        title=dict(text='Onderwerpen',x=0.5),
        xaxis=dict(),
        yaxis=dict(title='aantal moties',gridcolor='#EEEEEE',zerolinecolor='#EEEEEE',tickformat='d'),
        bargap=0.5,
        barmode='stack',
        plot_bgcolor='#FFFFFF'
    )
)

#propose
propose=pd.DataFrame(propose,columns=['proposer','topic','pnum'])
propose=propose.groupby(['proposer','topic']).sum().reset_index()
propose=propose.pivot(index='proposer',columns='topic',values='pnum').fillna(0)

traces=[]
for p in propose.index:
    traces.append(go.Scatterpolar(r=propose.loc[p], theta=propose.columns, fill='toself', name=p))
fig_pro=go.Figure(
    data=traces,
    layout=go.Layout(
        title=dict(text='Verdeling onderwerpen van moties',x=0.5),
        polar=dict(radialaxis=dict(range=[0,2.1],gridcolor='#C6C6C6',tickformat='d'),
                    angularaxis=dict(gridcolor='#C6C6C6'),bgcolor='#FFFFFF'),
        height=487
))

#pvotes
pvotes=pd.DataFrame(pvotes,columns=['party','topic','attitude','vnum'])
pvotes=pvotes.groupby(['party','topic','attitude'])['vnum'].sum().unstack('party').fillna(0)

fig_PVs={}
for t in topics:
    fig_PVs[t]=go.Figure(
        data=[
            go.Bar(y=pvotes.columns, x=pvotes.loc[t,'support'].values, name='voor',orientation='h',marker_color='#A6C4FE'),
            go.Bar(y=pvotes.columns, x=pvotes.loc[t,'against'].values, name='tegen', orientation='h',marker_color='#DDDDDD')],
        layout=go.Layout(
            title=dict(text='Stemuitslag aangaande '+ str(t)+' onderwerp',x=0.5),
            xaxis=dict(title='aantal moties',tickformat='d'),
            yaxis=dict(),
            #bargap=0.5,
            barmode='stack',
            plot_bgcolor='#FFFFFF',
            height=450
        )
    )

# correlations
corr = data.iloc[:,5:].corr()
fig_corr = go.Figure(
    data = (
        go.Heatmap(
        zmin=-1,
        zmax=1,
        z=corr,
        x= parties,
        y = parties,
        colorscale='RdBu'
        )
    ),
    layout = go.Layout(
        title=dict(text = 'Overeenkomst tussen partijen',x=0.5),
    )
)

# proposals per party
proposers={}
ps_x=[]
ps_y=[]
party_list={}
r3=request.urlopen('https://raw.githubusercontent.com/founting/votes/master/Party_list.csv')
lines=r3.readlines()
for line in lines[1:]:
    line_data=line.decode('utf-8').split(',')
    party_list[line_data[0]]=line_data[1].strip('\r\n')

r2=request.urlopen('https://raw.githubusercontent.com/founting/votes/master/proposals.csv')
lines=r2.readlines()
for line in lines[1:]:
    line_data=line.decode('utf-8').split(',')
    for j in range(4,len(line_data),2):
        proposer=line_data[j][1:]
        proposer=proposer.strip('\n')
        for key in party_list:
            if key.lower() in proposer.lower():
                if party_list[key] not in proposers:
                    proposers[party_list[key]]=1
                else:
                    proposers[party_list[key]]+=1
                break
for key in proposers:
    ps_x.append(key)
    ps_y.append(proposers[key])
#plot fig5
fig_ps=go.Figure(
    data=[
        go.Bar(x=ps_x, y=ps_y,marker_color='#82CDBD')],
    layout=go.Layout(
        title=dict(text='Aantal moties per partij',x=0.5),
        yaxis=dict(gridcolor='#EEEEEE',zerolinecolor='#EEEEEE',tickformat='d',dtick=200),
        plot_bgcolor='#FFFFFF',
        bargap=0.6,
    )
)


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__,external_stylesheets=external_stylesheets)
server=app.server

# html
app.title = "Dashboard Tweede Kamer"
app.layout = html.Div(children=[
    html.H1(children='Stemmen in de Tweede Kamer',
            style={'width':'99%','height':30,'fontSize': 20,'color':'#FFFFFF',
            'paddingLeft':'1.5%','paddingTop':5,'backgroundColor':'#363880'}),
    
    html.Div([
        dcc.Graph(id='fig_td',figure=fig_td)],
        style={'width':'47%','marginTop':10,'marginLeft':'2%','display':'inline-block','vertical-align':'top'}),
    
    html.Div([
        dcc.Graph(id='fig_corr', figure=fig_corr)],
        style={'width':'47%','marginTop':10,'marginLeft':'2%', 'marginRight':'2%','display':'inline-block','vertical-align':'top'}),

    html.Div([
        dcc.Dropdown(
            id='figPV_dropdown',
            options=[{'label':i, 'value':i} for i in topics],
            value='Housing',
            style={'height':37}),
        dcc.Graph(id='fig_pv')],
        style={'width':'47%','marginTop':25,'marginLeft':'2%','display':'inline-block','vertical-align':'top'}),
   
    html.Div([
        dcc.Graph(id='fig_pro',figure = fig_pro)],
        style={'width': '47%','marginTop':25,'marginLeft':'2%','marginRight':'2%','display': 'inline-block','vertical-align':'top'}),

    html.Div([
        dcc.Graph(id='fig_ps',figure=fig_ps)],
        style={'width':'96%','height':470,'marginTop':25,'marginBottom':15,'marginLeft':'2%','marginRight':'2%'})
],   
    style={'backgroundColor':'#F6F6F6'})

@app.callback(
    Output('fig_pv','figure'),
    [Input('figPV_dropdown','value')])

def update_graph(t):
    return fig_PVs[t]


if __name__ == '__main__':
    app.run_server()
