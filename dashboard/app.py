"""Dashboard independiente: lee CSV existentes, no recalcula backtest."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
st.set_page_config(page_title='Lab 03 | Statistical Arbitrage',layout='wide')
# Navigation-only presentation mode. Analysis mode below remains unchanged.
mode = st.sidebar.radio('Modo del dashboard', ['Exposición', 'Análisis completo'])
if mode == 'Exposición':
    import plotly.express as px
    st.title('Lab 03 | Arbitraje estadístico')
    sources = sorted((ROOT / 'artifacts').glob('*_backtest.csv'))
    if not sources:
        st.warning('Faltan resultados. Ejecuta python main.py desde la carpeta principal.'); st.stop()
    pairs = [f.stem.removesuffix('_backtest') for f in sources]
    pages = ['1 · Objetivo y selección', '2 · Kalman, VECM y Johansen',
             '3 · Backtesting y walk-forward', '4 · Conclusiones']
    page = st.sidebar.radio('Sección de la presentación', pages)
    chosen_p = st.sidebar.selectbox('Par', pairs,
          index=pairs.index('NWS_NWSA') if 'NWS_NWSA' in pairs else 0)
    p_df = pd.read_csv(ROOT / 'artifacts' / f'{chosen_p}_backtest.csv',parse_dates=['date']).set_index('date')
    metrics_file = ROOT / 'artifacts' / 'metrics.csv'
    metrics = pd.read_csv(metrics_file) if metrics_file.exists() else pd.DataFrame()
    record = metrics.loc[metrics.pair == chosen_p].iloc[0] if 'pair' in metrics and (metrics.pair == chosen_p).any() else None
    st.progress((pages.index(page)+1)/len(pages))
    if page == pages[0]:
        st.header('Objetivo y justificación económica')
        st.write('Investigar tres pares de activos con una relación económica defendible, construir una estrategia de reversión y evaluar su desempeño después de comisiones.')
        cols = st.columns(3)
        descriptions = [
            ('NWS–NWSA','Acciones de doble clase de News Corp; filtro inicial favorable.'),
            ('GOOG–GOOGL','Acciones de doble clase de Alphabet; Johansen principal no confirmó rango 1.'),
            ('TLT–VGLT','ETF de bonos del Tesoro; no superó el ajuste por pruebas múltiples.')]
        for col, (name,why) in zip(cols,descriptions):
            with col:
                st.markdown('**'+name+'**');st.caption(why)
        st.warning('Los pares son candidatos de investigación, no tres relaciones robustamente cointegradas fuera de muestra.')
        fig=go.Figure()
        for col in ('price_a','price_b'):
            if col in p_df:fig.add_scatter(x=p_df.index,y=p_df[col],name=col)
        fig.update_layout(title=f'Precios históricos: {chosen_p}',height=340)
        st.plotly_chart(fig,width='stretch')
    elif page == pages[1]:
        st.header('De la cointegración a las decisiones de trading')
        st.markdown('**Johansen** identifica un vector inicial; **Kalman 1** actualiza pesos dinámicos; **VECM** estima innovaciones con coeficientes entrenados; **Kalman 2** normaliza señales usando estadísticas anteriores a la actualización.')
        st.info('La varianza de Kalman 2 se estima con EWMA, no como segundo estado gaussiano. La proyección del error VECM usa pesos rezagados; el VECM mantiene su beta fija de entrenamiento.')
        tab1,tab2,tab3=st.tabs(['Spread y z-score','Pesos y ganancias','Johansen móvil'])
        with tab1:
            for fields,title in [(['spread_dynamic'],'Spread dinámico'),(['kalman2_z'],'Z-score de innovaciones')]:
                fig=go.Figure()
                for field in fields:
                    if field in p_df:fig.add_scatter(x=p_df.index,y=p_df[field],name=field)
                if fields[0]=='kalman2_z':
                    for level in (-2,2,-.5,.5):fig.add_hline(y=level,line_dash='dot')
                fig.update_layout(title=title,height=280)
                st.plotly_chart(fig,width='stretch')
        with tab2:
            for fields,title in [(['beta_a','beta_b'],'Pesos de Kalman 1'),
                                 (['kalman1_gain_a','kalman1_gain_b','kalman2_gain'],'Ganancias de Kalman')]:
                fig=go.Figure()
                for field in fields:
                    if field in p_df:fig.add_scatter(x=p_df.index,y=p_df[field],name=field)
                fig.update_layout(title=title,height=290)
                st.plotly_chart(fig,width='stretch')
        with tab3:
            jf=ROOT/'artifacts'/f'{chosen_p}_johansen_movil.csv'
            if jf.exists():
                j=pd.read_csv(jf,parse_dates=['date'])
                st.plotly_chart(px.line(j,x='date',y='beta_b',title='Eigenvector móvil · 504 sesiones, cada 21'),width='stretch')
                ok=j.loc[j.trace_rank.notna()]
                st.caption(f'Rango 1 en {int((ok.trace_rank==1).sum())} de {len(ok)} ventanas estimadas; solo diagnóstico.')
            else:st.info('Ejecuta python main.py para generar Johansen móvil.')
    elif page == pages[2]:
        st.header('Resultados y comparación fuera de muestra')
        if record is not None:
            cols=st.columns(4)
            for col,key,label in zip(cols,['sharpe','sortino','max_drawdown','commissions'],
                                     ['Sharpe OOS','Sortino','Max DD','Comisiones']):
                if key in record:
                    x=float(record[key]);fmt=f'${x:,.0f}' if key=='commissions' else (f'{x:.2%}' if key=='max_drawdown' else f'{x:.2f}')
                    col.metric(label,fmt)
        if 'equity' in p_df:
            fig=px.line(p_df.reset_index(),x='date',y='equity',title='Curva de capital: política base')
            fig.update_layout(height=300);st.plotly_chart(fig,width='stretch')
        wf_file=ROOT/'artifacts'/'walkforward_oos_comparison.csv'
        if wf_file.exists():
            from performance.walkforward_dashboard import load_comparison
            try:wf=load_comparison(wf_file,chosen_p)
            except (ValueError,pd.errors.ParserError) as err:
                st.error(f'No se pudo leer walk-forward: {err}');wf=None
            if wf is not None and not wf.empty:
                fig=px.bar(wf,x='periodo',y='rendimiento_pct',color='politica',barmode='group',
                           title='Rendimiento neto por partición (%)')
                fig.update_layout(height=330);st.plotly_chart(fig,width='stretch')
                st.dataframe(wf[['periodo','politica','entry_z','exit_z','rendimiento_pct','sharpe','commission']],
                             hide_index=True,width='stretch')
            else:st.info('No hay resultados walk-forward para este par.')
        else:st.info('Ejecuta python calibrar_walkforward.py para generar la comparación.')
    else:
        st.header('Conclusiones defendibles')
        st.markdown('''**Hallazgos**

- Los umbrales calibrados exclusivamente con entrenamiento redujeron las pérdidas y los costos registrados fuera de muestra.
- Los rendimientos netos de los tres candidatos siguieron siendo negativos.
- Johansen móvil y los diagnósticos por partición mostraron inestabilidad estadística.
- Las pruebas automatizadas respaldan componentes del software, no garantizan rentabilidad.

**Limitaciones:** inestabilidad de cointegración, pruebas múltiples, costos de transacción, supuestos de préstamo de acciones y aproximación EWMA para la varianza del segundo filtro. Sin Risk Parity por indicación del profesor.''')
    st.sidebar.caption('Selecciona Análisis completo para conservar la bitácora, filtros y visualizaciones originales.')
    st.stop()

st.title('Lab 03 · Cointegración, Kalman y VECM')
files=sorted((ROOT/'artifacts').glob('*_backtest.csv'))
if not files:
    st.warning('No hay artefactos. Ejecuta `python main.py` desde la raíz del proyecto.');st.stop()
chosen=st.selectbox('Par', [f.stem.replace('_backtest','') for f in files])
view=st.radio('Vista', ['Ejecutiva','Técnica'],horizontal=True)
df=pd.read_csv(ROOT/'artifacts'/f'{chosen}_backtest.csv',parse_dates=['date']).set_index('date')
metrics_path=ROOT/'artifacts'/'metrics.csv';m=pd.read_csv(metrics_path);row=m.loc[m.pair==chosen].iloc[0]
if view=='Ejecutiva':
    cols=st.columns(6)
    for col,(label,key) in zip(cols,[('Sharpe','sharpe'),('Sortino','sortino'),('Calmar','calmar'),('Max DD','max_drawdown'),('Comisiones','commissions'),('Préstamo','borrow_cost')]):
        col.metric(label,f'{row[key]:,.3f}' if key not in ('commissions','borrow_cost','max_drawdown') else (f'{row[key]:.2%}' if key=='max_drawdown' else f'${row[key]:,.0f}'))
    fig=go.Figure();fig.add_scatter(x=df.index,y=df.equity,name='Capital');fig.update_layout(title='Curva de capital',height=340);st.plotly_chart(fig,width='stretch')
    fig=go.Figure();fig.add_scatter(x=df.index,y=df.drawdown,name='Drawdown',fill='tozeroy');fig.update_layout(title='Drawdown');st.plotly_chart(fig,width='stretch')
    st.bar_chart(pd.DataFrame({'Comisiones':[df.commission.sum()],'Costo préstamo':[df.borrow.sum()]},index=['Costos']))
    # Comparación ya precalculada por calibrar_walkforward.py: no ejecuta ajustes en Streamlit.
    st.subheader('Walk-forward · Original vs. calibrada')
    st.caption('Umbrales seleccionados SOLO en entrenamiento. Prueba y validación son evaluación fuera de muestra; no utilizarlos para reoptimizar.')
    from performance.walkforward_dashboard import load_comparison, commission_savings
    wf_path = ROOT/'artifacts'/'walkforward_oos_comparison.csv'
    try:
        wf = load_comparison(wf_path, chosen)
    except (ValueError, pd.errors.ParserError) as exc:
        st.error(f'No se pudo leer la comparación walk-forward: {exc}')
        wf = None
    if wf is None:
        st.info('No se encontró walkforward_oos_comparison.csv. Ejecuta `python calibrar_walkforward.py` desde la raíz del proyecto.')
    elif wf.empty:
        st.info('El CSV walk-forward no contiene resultados para este par.')
    else:
        st.dataframe(wf[['periodo','politica','entry_z','exit_z','rendimiento_pct','sharpe','drawdown_pct','commission','borrow','trade_days']]
            .rename(columns={'periodo':'Periodo','politica':'Política','entry_z':'Entrada z','exit_z':'Salida z',
                             'rendimiento_pct':'Retorno neto (%)','sharpe':'Sharpe','drawdown_pct':'Max DD (%)',
                             'commission':'Comisiones ($)','borrow':'Préstamo ($)','trade_days':'Días con transacción'}),
            hide_index=True, width='stretch')
        import plotly.express as px
        order=['Prueba','Validación']
        chart=px.bar(wf,x='periodo',y='rendimiento_pct',color='politica',barmode='group',
                     category_orders={'periodo':order},labels={'periodo':'Periodo',
                       'rendimiento_pct':'Rendimiento neto (%)','politica':'Política'},
                     title='Rendimiento neto fuera de muestra por periodo')
        st.plotly_chart(chart,width='stretch')
        chart2=px.bar(wf,x='periodo',y='commission',color='politica',barmode='group',
                      category_orders={'periodo':order},labels={'periodo':'Periodo','commission':'Comisiones ($)',
                       'politica':'Política'},title='Costo de comisiones: original y calibrada')
        st.plotly_chart(chart2,width='stretch')
        savings=commission_savings(wf)
        if not savings.empty:
            st.caption('Ahorro de comisiones de calibrada frente a original: '+
                ' · '.join(f"{('Prueba' if k=='test' else 'Validación')}: ${v:,.2f}" for k,v in savings.items()))
        st.caption('Los retornos son por partición. No deben sumarse para obtener el acumulado. La comparación es retrospectiva; no modifica los CSV originales ni la política en main.py.')

    st.subheader('Bitácora por operación')
    ops_file=ROOT/'artifacts'/f'{chosen}_operaciones.csv'
    if ops_file.exists():
        ops=pd.read_csv(ops_file,parse_dates=['entry_date','exit_date'])
        if ops.empty:
            st.info('Sin operaciones registradas para este par.')
        else:
            left,mid,right=st.columns(3)
            with left:
                parts=st.multiselect('Partición de entrada',sorted(ops.entry_partition.dropna().unique().tolist()),default=sorted(ops.entry_partition.dropna().unique().tolist()))
            with mid:
                dirs=st.multiselect('Dirección',sorted(ops.direction.dropna().unique().tolist()),default=sorted(ops.direction.dropna().unique().tolist()))
            with right:
                statuses=st.multiselect('Estado',sorted(ops.status.dropna().unique().tolist()),default=sorted(ops.status.dropna().unique().tolist()))
            outcomes=st.multiselect('Resultado neto',['Ganadora','Perdedora','Cero'],default=['Ganadora','Perdedora','Cero'])
            marked=np.select([ops.net_pnl>1e-9,ops.net_pnl< -1e-9],['Ganadora','Perdedora'],default='Cero')
            selection=ops[ops.entry_partition.isin(parts)&ops.direction.isin(dirs)&ops.status.isin(statuses)&pd.Series(marked,index=ops.index).isin(outcomes)].copy()
            closed=selection[selection.status=='cerrada'].copy()
            n_wins=int((closed.net_pnl>0).sum())
            gp=float(closed.loc[closed.net_pnl>0,'net_pnl'].sum())
            gl=float(-closed.loc[closed.net_pnl<0,'net_pnl'].sum())
            profit_factor=gp/gl if gl>0 else (float('inf') if gp>0 else float('nan'))
            k1,k2,k3,k4=st.columns(4)
            k1.metric('Operaciones cerradas',f'{len(closed):,}')
            k2.metric('Win rate',f'{n_wins/len(closed):.1%}' if len(closed) else 'N/D')
            k3.metric('Profit factor',f'{profit_factor:.2f}' if np.isfinite(profit_factor) else 'N/D')
            k4.metric('P&L neto de selección',f'${selection.net_pnl.sum():,.2f}')
            st.dataframe(selection[['trade_id','entry_date','exit_date','status','direction','entry_partition','holding_days','entry_gross_notional','gross_pnl','commissions','borrow_cost','net_pnl','net_return_on_entry_gross','rebalance_days']],use_container_width=True,hide_index=True)
            st.caption('Una operación es un episodio desde entrada hasta salida; rebalanceos no crean una nueva operación. Las posiciones abiertas tienen P&L marcado a mercado, sin liquidación ficticia. El retorno es P&L neto / exposición bruta de entrada.')
            st.subheader('Distribución de retornos por operación cerrada')
            xs=closed.net_return_on_entry_gross.dropna().astype(float)
            if len(xs):
                chart=go.Figure()
                chart.add_histogram(x=xs,nbinsx=35,histnorm='probability density',name='Retornos por operación',opacity=.75)
                sigma=float(xs.std(ddof=1)) if len(xs)>1 else 0.
                if sigma>1e-12:
                    xx=np.linspace(float(xs.min()),float(xs.max()),200)
                    mu=float(xs.mean())
                    yy=np.exp(-.5*((xx-mu)/sigma)**2)/(sigma*np.sqrt(2*np.pi))
                    chart.add_scatter(x=xx,y=yy,name='Normal de referencia',mode='lines')
                chart.update_layout(xaxis_title='Retorno neto / nocional bruto inicial',yaxis_title='Densidad',height=330,barmode='overlay')
                st.plotly_chart(chart,width='stretch')
            else:
                st.info('No hay operaciones cerradas con los filtros seleccionados.')
            st.download_button('Exportar operaciones filtradas (CSV)',selection.to_csv(index=False).encode('utf-8'),file_name=f'{chosen}_operaciones_filtradas.csv',mime='text/csv')
    else:
        st.info('Bitácora pendiente. Ejecuta desde la raíz: `python generar_bitacoras.py` (después de `python main.py`).')
    with st.expander('Registro diario (auditoría)'):
        period=st.multiselect('Particiones',df.partition.unique().tolist(),default=df.partition.unique().tolist())
        direction=st.multiselect('Posiciones',[-1,0,1],default=[-1,0,1])
        st.dataframe(df[df.partition.isin(period)&df.position.isin(direction)][['partition','position','trade_notional','commission','borrow','equity']])

else:
    def plot(columns,title,threshold=False):
        fig=go.Figure()
        for c in columns:fig.add_scatter(x=df.index,y=df[c],name=c)
        if threshold:
            for val in [-2,2,-.5,.5]:fig.add_hline(y=val,line_dash='dot')
        fig.update_layout(title=title,height=360);st.plotly_chart(fig,width='stretch')
    plot(['price_a','price_b'],'Precios ajustados')
    plot(['spread_dynamic'],'Spread y señales (consultar señal en tabla)')
    plot(['beta_a','beta_b'],'Pesos dinámicos beta')
    plot(['kalman1_gain_a','kalman1_gain_b','kalman2_gain'],'Ganancias de Kalman')
    plot(['kalman2_z'],'Z-score de innovaciones VECM',True)
    plot(['kalman1_uncertainty','kalman2_uncertainty'],'Varianzas posteriores (escalas distintas)')
    sr=df['return'].rolling(252).mean()/df['return'].rolling(252).std()*np.sqrt(252)
    fig=go.Figure(go.Scatter(x=df.index,y=sr,name='Sharpe móvil'))
    fig.update_layout(title='Sharpe móvil 252 días');st.plotly_chart(fig,width='stretch')
    # Serie de Johansen móvil precalculada por main.py (no se vuelve a estimar aquí).
    rolling_path = ROOT/'artifacts'/f'{chosen}_johansen_movil.csv'
    if rolling_path.exists():
        jmov = pd.read_csv(rolling_path, parse_dates=['date']).set_index('date')
        fig = go.Figure()
        fig.add_scatter(x=jmov.index,y=jmov['beta_b'],name='Eigenvector: beta_b (beta_a=1)',mode='lines+markers')
        fig.update_layout(title='Primer eigenvector de Johansen móvil (504 días; cada 21)',height=350,
                          xaxis_title='Fecha de cierre de ventana',yaxis_title='Peso normalizado beta_b')
        st.plotly_chart(fig,width='stretch')
        good = jmov[jmov['trace_rank'].notna()]
        if len(good):
            st.caption(f'Rango 1 por traza en {int((good.trace_rank==1).sum())} de {len(good)} ventanas válidas; la serie es diagnóstica y no determina las señales.')
        if jmov['error'].astype(str).str.len().gt(0).any():
            st.warning('Algunas ventanas de Johansen no pudieron estimarse; revisa el CSV del par.')
    else:
        st.info('Falta la serie de Johansen móvil. Ejecuta de nuevo `python main.py` para generarla.')
    st.caption('Bitácora por operación: disponible en la vista Ejecutiva después de generar los CSV con generar_bitacoras.py.')
