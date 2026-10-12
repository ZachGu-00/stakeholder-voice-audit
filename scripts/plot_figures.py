"""Draw the manuscript figures using figures4papers conventions."""
from dataclasses import dataclass
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, PathPatch, Polygon, Rectangle
from matplotlib.path import Path as MPath

import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--font', default='Times New Roman')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/reproduced/figures'
H = S = ROOT/'results/reference'
OUT.mkdir(parents=True, exist_ok=True)
PALETTE = dict(blue_main='#0F4D92', blue_secondary='#3775BA', green_1='#DDF3DE',
               green_2='#AADCA9', green_3='#8BCF8B', red_1='#F6CFCB', red_2='#E9A6A1',
               red_strong='#B64342', neutral='#CFCECE', highlight='#FFD700',
               teal='#42949E', violet='#9A4D8E')
BLUE, TEAL, RED = [PALETTE[k] for k in ['blue_main', 'teal', 'red_strong']]
INK, MUTED, GRID, PALE = '#1D2D3F', '#586779', '#E5EAF0', '#F3F6FA'
VERSIONS = [('rater_1', BLUE, 'o'), ('rater_2', TEAL, 's')]
FILES, PLOTTED = [], {}

@dataclass(frozen=True)
class FigureStyle:
    font_size: int = 15
    axes_linewidth: float = 1.5
    use_tex: bool = False
    font_family: tuple = ('Times New Roman',)

def apply_publication_style(style=FigureStyle()):
    for filename in ['times.ttf', 'timesbd.ttf', 'timesi.ttf', 'timesbi.ttf']:
        path = Path('C:/Windows/Fonts') / filename
        if path.exists(): font_manager.fontManager.addfont(str(path))
    font_manager.findfont(args.font, fallback_to_default=False)
    plt.rcParams.update({'font.family': [args.font], 'font.size': style.font_size,
        'axes.linewidth': style.axes_linewidth, 'axes.spines.top': False,
        'axes.spines.right': False, 'axes.titleweight': 'bold', 'axes.titlesize': 18,
        'axes.labelsize': 15, 'axes.titlepad': 17, 'legend.frameon': False,
        'legend.fontsize': 13, 'pdf.fonttype': 42, 'svg.fonttype': 'none',
        'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': MUTED,
        'ytick.color': INK, 'axes.edgecolor': MUTED, 'text.usetex': style.use_tex,
        'xtick.major.size': 4, 'ytick.major.size': 0, 'savefig.facecolor': 'white'})

def create_subplots(nrows=1, ncols=1, figsize=None, **kwargs):
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, **kwargs)
    return fig, np.asarray(axes, dtype=object).reshape(-1)

def finalize_figure(fig, out_path, formats=('pdf', 'svg', 'png'), dpi=300, close=True):
    supported = {'pdf', 'svg', 'eps', 'png', 'jpg', 'jpeg', 'tif', 'tiff'}
    assert set(formats) <= supported
    saved = []
    for ext in formats:
        path = Path(out_path).with_suffix('.' + ext)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=dpi, facecolor='white')
        saved.append(path)
    if close:
        plt.close(fig)
    FILES.extend(saved)
    return saved

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

prev, contrasts, survey = [read(p) for p in [H/'prevalence.csv', H/'contrasts.csv', S/'joint_plot_data.csv']]
def select(rows, **criteria):
    matches = [r for r in rows if all(r[k] == v for k, v in criteria.items())]
    assert len(matches) == 1, criteria
    return matches[0]

def pget(v, f, c):
    return select(prev, scope='all_noncalibration', coding_version=v,
                  group_type='overall', feature=f, condition=c)

def cget(v, f, kind='overall', value='all'):
    return select(contrasts, scope='all_noncalibration', coding_version=v,
                  group_type=kind, group_value=value, feature=f, contrast='B_minus_A')

def values(row):
    val, lo, hi = np.array([float(row[k]) for k in ['estimate', 'ci_low', 'ci_high']]) * 100
    assert np.isfinite([val, lo, hi]).all() and lo <= val <= hi
    return val, lo, hi

def tidy(ax, rows=None):
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.grid(axis='x', color=GRID, lw=.85)
    ax.set_axisbelow(True)
    ax.tick_params(axis='y', pad=9)
    if rows is not None:
        for i, y in enumerate(rows):
            if i % 2 == 0:
                ax.axhspan(y-.43, y+.43, color=PALE, zorder=0)

def errorpoint(ax, row, y, color, marker, filled=True):
    val, lo, hi = values(row)
    ax.errorbar(val, y, xerr=[[val-lo], [hi-val]], fmt=marker,
                color=color, mfc=color if filled else 'white', mec=color, mew=1.6,
                ms=7, lw=1.7, capsize=3.2, zorder=4)
    return val

def version_handles():
    return [Line2D([], [], marker=m, color=c, lw=1.8, ms=7,
                   mfc=c if i == 0 else 'white', mew=1.5, label=f'Coding version {i+1}')
            for i, (_, c, m) in enumerate(VERSIONS)]

apply_publication_style()

def line(ax, points, color=BLUE, lw=2, **kwargs):
    p = np.asarray(points)
    ax.plot(p[:, 0], p[:, 1], color=color, lw=lw, solid_capstyle='round', **kwargs)

def box(ax, x, y, w, h, fc='white', ec=GRID, radius=.15, lw=1.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0.02,rounding_size={radius}',
                              fc=fc, ec=ec, lw=lw))

def arrow(ax, start, end, color=MUTED, dashed=False, rad=0, lw=1.7):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>', mutation_scale=14,
                 color=color, lw=lw, linestyle=(0, (4, 3)) if dashed else '-',
                 connectionstyle=f'arc3,rad={rad}', shrinkA=3, shrinkB=3))

def person(ax, x, y, scale=.65, color=BLUE):
    ax.add_patch(Circle((x, y+.70*scale), .18*scale, fc='white', ec=color, lw=2))
    p = MPath([(x-.40*scale, y), (x-.37*scale, y+.58*scale),
               (x+.37*scale, y+.58*scale), (x+.40*scale, y)],
             [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4])
    ax.add_patch(PathPatch(p, fc='none', ec=color, lw=2, capstyle='round'))

def heart(ax, x, y, size=.5, color=RED):
    vertices = np.array([(0,-.65),(-1,.02),(-.8,.75),(0,.35),(.8,.75),(1,.02),(0,-.65)]) * size + [x,y]
    ax.add_patch(PathPatch(MPath(vertices, [MPath.MOVETO]+[MPath.CURVE4]*6), fc=color, ec=color, lw=1))

def sheet(ax, x, y, w=.65, h=.9, color=BLUE, checks=False):
    box(ax, x-w/2, y-h/2, w, h, ec=color, radius=.055, lw=1.7)
    for yy in [y+h*.24, y, y-h*.24]:
        if checks:
            line(ax, [(x-w*.32, yy), (x-w*.25, yy-.06), (x-w*.13, yy+.07)], color, 1.4)
            line(ax, [(x-w*.02, yy), (x+w*.29, yy)], color, 1.2)
        else:
            line(ax, [(x-w*.28, yy), (x+w*.28, yy)], color, 1.5)

def shield(ax, x, y, s=.5, color=BLUE):
    pts=np.array([(-.65,.55),(0,.80),(.65,.55),(.55,-.3),(0,-.8),(-.55,-.3)])*s+[x,y]
    ax.add_patch(Polygon(pts, fc='white', ec=color, lw=1.8, joinstyle='round'))
    line(ax, [(x-.2*s,y),(x-.03*s,y-.2*s),(x+.27*s,y+.2*s)],color,1.7)

def school(ax, x, y, s=.85):
    ax.add_patch(Polygon(np.array([(-.7,.4),(0,.85),(.7,.4)])*s+[x,y], fc=PALE, ec=BLUE, lw=1.6))
    ax.add_patch(Rectangle((x-.6*s,y-.42*s),1.2*s,.82*s,fc='white',ec=BLUE,lw=1.6))
    for xx in [-.38, .38]:
        ax.add_patch(Rectangle((x+(xx-.1)*s,y+.03*s),.2*s,.2*s,fc=PALETTE['green_1'],ec=BLUE,lw=1))
    ax.add_patch(Rectangle((x-.13*s,y-.42*s),.26*s,.45*s,fc=PALE,ec=BLUE,lw=1))

fig, (ax,) = create_subplots(figsize=(13.4, 6.9))
ax.set(xlim=(0,16), ylim=(0,8.25), aspect='equal'); ax.axis('off')
ax.text(.15,7.95,'a',fontweight='bold',fontsize=22)
ax.text(.55,7.97,'From school concerns to actionable replies',fontweight='bold',fontsize=19)
stages=[(.25,2.35,'School scenario'),(3.05,2.65,'Prompt modules'),(6.15,1.75,'AI assistant'),
        (8.35,3.5,'Reply functions'),(12.55,3.15,'School connection')]
for x,w,title in stages:
    ax.text(x+w/2,7.23,title,ha='center',fontweight='bold',fontsize=15)
    box(ax,x,3.55,w,3.28,fc=PALE if x<8 else 'white')
person(ax,.92,4.48,.87)
box(ax,1.13,5.38,1.05,.7,fc='white',ec=BLUE,radius=.14)
line(ax,[(1.3,5.55),(1.9,5.55)],BLUE,1.3)
line(ax,[(1.3,5.83),(1.77,5.83)],BLUE,1.3)
ax.text(1.43,4.11,'60 scenarios',ha='center',fontsize=14)
ax.text(4.55,6.48,'Procedure',ha='center',fontsize=13,color=MUTED)
ax.text(4.03,6.1,'−',ha='center',fontsize=18)
ax.text(5.03,6.1,'+',ha='center',fontsize=18)
ax.text(3.27,5.08,'Boundary',rotation=90,ha='center',va='center',fontsize=12,color=MUTED)
for row in range(2):
    for col in range(2):
        x,y=3.6+col,5.02-row*.92
        color=BLUE if col else RED
        box(ax,x,y,.84,.75,fc='#EAF1FA' if col else '#FCEFEB',ec=color if row==0 else GRID,radius=.07,lw=1.5)
        ax.text(x+.42,y+.38,'ABCD'[row*2+col],ha='center',va='center',fontsize=17,
                color=color if row==0 else MUTED,fontweight='bold')
ax.text(3.46,5.4,'−',fontsize=14,ha='center',va='center')
ax.text(3.46,4.48,'+',fontsize=14,ha='center',va='center')
for offset in [.17,.08,0]:
    box(ax,6.47+offset,4.85+offset,.95,1.03,fc='white',ec=BLUE,radius=.08,lw=1.4)
for lx in [6.64,7.15]:
    for yy in [5.09,5.52]:
        ax.add_patch(Circle((lx,yy),.065,fc=BLUE,ec='none'))
for yy in [5.09,5.52]:
    for yy2 in [5.09,5.52]:
        line(ax,[(6.7,yy),(7.09,yy2)],BLUE,.9)
ax.text(7.02,4.35,'3 models',ha='center',fontsize=14)
ax.text(7.02,3.93,'720 replies',ha='center',fontsize=14,color=MUTED)
heart(ax,9.1,5.99,.37,RED)
ax.text(9.1,5.27,'Recognise',ha='center',fontsize=14)
ax.text(10.06,5.93,'+',ha='center',va='center',fontsize=22,color=MUTED)
sheet(ax,11.02,5.98,.56,.7,BLUE,True)
ax.text(11.02,5.27,'Guide',ha='center',fontsize=14)
line(ax,[(9.12,4.89),(9.12,4.71),(11.06,4.71),(11.06,4.89)],BLUE,1.5)
arrow(ax,(10.09,4.71),(10.09,4.41),BLUE)
for x,label in [(8.85,'Record'),(10.08,'Contact'),(11.33,'Review')]:
    ax.add_patch(Circle((x,4.11),.18,fc=BLUE,ec='none'))
    ax.text(x,4.11,str([8.85,10.08,11.33].index(x)+1),ha='center',va='center',color='white',fontsize=11)
    ax.text(x,3.72,label,ha='center',fontsize=12)
arrow(ax,(9.11,4.11),(9.82,4.11),BLUE,lw=1.2)
arrow(ax,(10.35,4.11),(11.07,4.11),BLUE,lw=1.2)
school(ax,14.14,6.04,.79)
person(ax,13.37,4.62,.60,TEAL);person(ax,14.9,4.62,.60,TEAL)
line(ax,[(13.37,5.25),(13.37,5.46),(14.9,5.46),(14.9,5.25)],TEAL,1.6)
shield(ax,14.14,4.53,.36,TEAL)
ax.text(14.14,3.91,'Human follow-through',ha='center',fontsize=13)
for x1,x2 in [(2.60,3.03),(5.72,6.13),(7.92,8.33)]:
    arrow(ax,(x1,5.38),(x2,5.38),BLUE)
arrow(ax,(11.88,5.38),(12.53,5.38),TEAL,True)
ax.text(.15,2.98,'b',fontweight='bold',fontsize=22)
ax.text(.55,3.0,'Stakeholder expectations',fontweight='bold',fontsize=19)
box(ax,.25,.36,15.45,2.2,fc=PALE,ec=GRID,radius=.16)
for x,label in [(1.0,'Students'),(2.08,'Parents'),(3.16,'Teachers'),(4.3,'Principals')]:
    person(ax,x,1.38,.59,BLUE)
    ax.text(x,1.03,label,ha='center',fontsize=12)
ax.text(2.65,.58,'27,396 respondents',ha='center',fontsize=15,fontweight='bold')
arrow(ax,(4.96,1.55),(5.75,1.55),BLUE)
sheet(ax,6.17,1.58,.62,.9,BLUE,True)
ax.text(7.94,2.13,'Same respondent',ha='center',fontsize=14,fontweight='bold')
ax.text(7.95,.57,'27,301 people',ha='center',fontsize=11,color=MUTED)
person(ax,7.47,1.0,.73,BLUE)
arrow(ax,(7.89,1.38),(8.67,1.84),BLUE,lw=1.3)
arrow(ax,(7.89,1.3),(8.67,.83),RED,lw=1.3)
heart(ax,8.93,1.90,.19,BLUE)
shield(ax,8.94,.82,.23,RED)
ax.text(9.33,1.88,'Help',va='center',fontsize=14)
ax.text(9.33,.82,'Concern',va='center',fontsize=14)
arrow(ax,(10.83,1.51),(11.54,1.51),TEAL,True)
heart(ax,12.18,1.68,.24,BLUE)
shield(ax,13.42,1.70,.32,TEAL)
person(ax,14.7,1.43,.5,TEAL)
ax.text(12.18,.94,'Support',ha='center',fontsize=13)
ax.text(13.42,.94,'Privacy',ha='center',fontsize=13)
ax.text(14.7,.94,'Human role',ha='center',fontsize=13)
line(ax,[(5.85,2.61),(5.85,3.33),(1.43,3.33)],MUTED,1.2,linestyle=(0,(4,3)))
arrow(ax,(1.43,3.33),(1.43,3.54),MUTED,True,lw=1.2)
arrow(ax,(14.15,2.62),(14.15,3.51),TEAL,True)
fig.subplots_adjust(left=.015,right=.985,bottom=.018,top=.985)
finalize_figure(fig,OUT/'fig01_actionable_support')
PLOTTED['figure1']={'type':'conceptual study and design schematic','counts':{'scenarios':60,'models':3,'generated_replies':720,'survey_respondents':27396},
    'solid_links':'study sequence and paired survey judgements','dashed_links':'thematic and interpretive connections; school follow-through is not an observed intervention outcome'}

features=['procedural_remedy','emotional_validation','institutional_stake_recognition','procedure_and_emotional_validation']
labels=['Concrete procedure','Emotional recognition','Institutional stakes','Procedure + emotion']
fig, (ax,bx)=create_subplots(1,2,figsize=(13.4,5.75),gridspec_kw={'width_ratios':[1,1.07]})
PLOTTED['figure2']={'prevalence':[],'matched_effects':[]}
for i,f in enumerate(features):
    for j,(v,_,marker) in enumerate(VERSIONS):
        y=i+(j-.5)*.23
        a,b=pget(v,f,'campus'),pget(v,f,'procedure')
        ax.plot([values(a)[0],values(b)[0]],[y,y],color='#CED8E3',lw=2.5,zorder=2)
        errorpoint(ax,a,y,RED,marker,j==0)
        errorpoint(ax,b,y,BLUE,marker,j==0)
        PLOTTED['figure2']['prevalence'].extend([a,b])
        r=cget(v,f); PLOTTED['figure2']['matched_effects'].append(r)
        errorpoint(bx,r,y,VERSIONS[j][1],marker,j==0)
    pair=[values(cget(v,f))[0] for v,_,_ in VERSIONS]
    bx.text(109,i,f'{pair[0]:+.1f} / {pair[1]:+.1f}',ha='right',va='center',fontsize=13)
for a in [ax,bx]:
    tidy(a,range(4));a.set(ylim=(3.53,-.57),yticks=range(4))
ax.set(yticklabels=labels,xlim=(-3,105),xticks=[0,25,50,75,100],xlabel='Replies with feature (%)')
bx.set(yticklabels=[],xlim=(-10,114),xticks=[0,20,40,60],xlabel='Procedural guidance minus default (pp)')
bx.spines['bottom'].set_bounds(-10,70)
bx.axvline(0,color=MUTED,lw=1.4,zorder=2)
ax.set_title('a  Recognition and concrete support',loc='left')
bx.set_title('b  Matched change',loc='left')
bx.text(109,-.55,'Version 1 / 2',ha='right',fontsize=12,color=MUTED)
conditions=[Line2D([],[],color=RED,marker='o',lw=0,ms=8,label='Default assistant'),
            Line2D([],[],color=BLUE,marker='o',lw=0,ms=8,label='Procedural guidance')]
fig.legend(handles=conditions,loc='lower left',bbox_to_anchor=(.165,.01),ncol=2,handletextpad=.5,columnspacing=1.5)
fig.legend(handles=version_handles(),loc='lower right',bbox_to_anchor=(.98,.01),ncol=2,handletextpad=.5,columnspacing=1.4)
fig.subplots_adjust(left=.20,right=.985,top=.855,bottom=.24,wspace=.17)
finalize_figure(fig,OUT/'fig02_human_support')

modelkeys=['GPT-5','Deepseek v4 flash','Claude Haiku 4.5']
modellabels=['GPT-5','Deepseek v4 flash','Claude Haiku 4.5']
categories=sorted({r['group_value'] for r in contrasts if r['group_type']=='category'})
categorylabels={'academic_pressure':'Academic pressure','bullying':'Bullying','relationship_skills':'Relationship skills',
    'responsible_decision':'Responsible decisions','self_awareness':'Self awareness','self_management':'Self management',
    'social_anxiety':'Social anxiety','social_awareness':'Social awareness'}
fig,(ax,bx)=create_subplots(1,2,figsize=(13.4,6.4),gridspec_kw={'width_ratios':[1,1.05]})
PLOTTED['figure3']=[]
for a,kind,keys,names,title in [(ax,'model',modelkeys,modellabels,'a  Across three models'),
      (bx,'category',categories,[categorylabels[k] for k in categories],'b  Across eight school themes')]:
    positions=np.linspace(0,7,len(keys)) if kind=='model' else np.arange(8)
    for i,(key,y) in enumerate(zip(keys,positions)):
        for j,(v,c,m) in enumerate(VERSIONS):
            r=cget(v,'procedural_remedy',kind,key);PLOTTED['figure3'].append(r)
            errorpoint(a,r,y+(j-.5)*.25,c,m,j==0)
    tidy(a,positions);a.axvline(0,color=MUTED,lw=1.4)
    a.set(yticks=positions,yticklabels=names,ylim=(7.6,-.6),xlim=(-5,105),xticks=[0,25,50,75,100],
          xlabel='Increase in concrete procedure (pp)')
    a.set_title(title,loc='left')
fig.legend(handles=version_handles(),loc='lower center',bbox_to_anchor=(.57,.008),ncol=2,columnspacing=2.5)
fig.subplots_adjust(left=.16,right=.985,top=.87,bottom=.19,wspace=.65)
finalize_figure(fig,OUT/'fig03_generalisation')

sr=[r for r in survey if r['threshold']=='primary'];assert len(sr)==7
sl=['Primary students: relief / privacy','Middle students: relief / privacy','Parents: support / privacy',
    'Parents: support / human role','Teachers: value / privacy','Teachers: value / relationships','Teachers: value / teacher role']
ys=np.array([0,1,2.55,3.55,5.1,6.1,7.1])
fig,(ax,bx)=create_subplots(1,2,figsize=(13.4,6.7),gridspec_kw={'width_ratios':[1.45,1]})
colors=[BLUE,PALETTE['green_2'],PALETTE['red_2'],PALETTE['neutral']]
leg=['Both endorsed','Benefit only','Concern only','Neither endorsed']
hatches=['','','//','..']
PLOTTED['figure4']=[]
for i,(r,y) in enumerate(zip(sr,ys)):
    n,x,c,b=[int(r[k]) for k in ['n_complete','n_benefit_agree','n_concern_agree','n_both']]
    counts=np.array([b,x-b,c-b,n-x-c+b]);assert counts.min()>=0 and counts.sum()==n
    widths=counts/n*100;assert np.isclose(widths.sum(),100)
    left=0
    for j,width in enumerate(widths):
        ax.barh(y,width,left=left,color=colors[j],height=.63,edgecolor='white',linewidth=.8,hatch=hatches[j],label=leg[j] if i==0 else None)
        if j==0:ax.text(width/2,y,f'{width:.1f}%',ha='center',va='center',fontsize=13,color='white',fontweight='bold')
        left+=width
    value=float(r['concern_among_benefit_pct']);assert abs(value-100*b/x)<.0001
    bx.hlines(y,0,value,color='#B8CBDD',lw=2.6)
    bx.plot(value,y,'o',color=BLUE,ms=8)
    bx.text(value+3,y,f'{value:.1f}%',va='center',fontsize=14,fontweight='bold')
    PLOTTED['figure4'].append({'source':r,'category_counts':counts.tolist(),'category_percentages':widths.tolist(),'conditional_percentage':value})
for a in [ax,bx]:
    tidy(a);a.set(ylim=(7.8,-.75),yticks=ys,xticks=[0,25,50,75,100],xlim=(0,102))
    for yy in [1.77,4.32]:a.axhline(yy,color=GRID,lw=1)
ax.set(yticklabels=sl,xlabel='Respondents to each item pair (%)')
bx.set(yticklabels=[],xlim=(0,109),xlabel='Concern among benefit endorsers (%)')
ax.set_title('a  Benefit and concern coexist',loc='left')
bx.set_title('b  Concern among supporters',loc='left')
fig.legend(*ax.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.61,.007),ncol=4,columnspacing=1.5,handlelength=1.7)
fig.subplots_adjust(left=.29,right=.985,top=.88,bottom=.20,wspace=.14)
finalize_figure(fig,OUT/'fig04_joint_expectations')

counts=read(ROOT/'data/survey_joint_counts.csv')
short=['Primary students\nRelief / privacy','Middle students\nRelief / privacy','Parents\nSupport / privacy','Parents\nSupport / human role',
       'Teachers\nValue / privacy','Teachers\nValue / relationships','Teachers\nValue / teacher role']
fig,axs=create_subplots(2,4,figsize=(13.4,7.25))
cmap=LinearSegmentedColormap.from_list('figures4papers_blue',['#FFFFFF','#DAE7F5','#70A0D0',BLUE])
PLOTTED['figure5']=[]
for i,(r,ax) in enumerate(zip(sr,axs)):
    cells=np.zeros((5,5),dtype=int);n=int(r['n_complete'])
    records=[c for c in counts if c['pair_id']==r['pair_id']];assert len(records)==25
    for c in records:cells[int(c['y_value'])-1,int(c['x_value'])-1]=int(c['n'])
    assert cells.sum()==n and cells[3:,3:].sum()==int(r['n_both'])
    pct=cells/n*100;assert pct.max()<=45
    im=ax.imshow(pct,origin='lower',vmin=0,vmax=45,cmap=cmap,interpolation='nearest')
    for yy in range(5):
        for xx in range(5):ax.text(xx,yy,f'{pct[yy,xx]:.0f}',ha='center',va='center',fontsize=12,color='white' if pct[yy,xx]>=29 else INK)
    ax.set_xticks(np.arange(-.5,5,1),minor=True);ax.set_yticks(np.arange(-.5,5,1),minor=True)
    ax.grid(which='minor',color='#FFFFFF',lw=1.2);ax.tick_params(which='minor',bottom=False,left=False)
    ax.add_patch(Rectangle((2.5,2.5),2,2,fill=False,ec=RED,lw=2.3,zorder=4))
    ax.set(xticks=range(5),xticklabels=range(1,6),yticks=range(5),yticklabels=range(1,6))
    ax.tick_params(labelsize=12,pad=5)
    ax.spines[['top','right','bottom','left']].set_visible(False)
    ax.set_title(chr(97+i)+'  '+short[i],loc='left',fontsize=15,pad=11,linespacing=1.2)
    if i>=4:ax.set_xlabel('Benefit / support',fontsize=13,labelpad=5)
    if i%4==0:ax.set_ylabel('Concern',fontsize=13,labelpad=6)
    PLOTTED['figure5'].append({'pair_id':r['pair_id'],'n_complete':n,'counts_y_concern_x_benefit':cells.tolist(),'cell_percentages':pct.tolist()})
legend=axs[-1];legend.axis('off')
legend.text(0,.96,'How to read',fontsize=17,fontweight='bold',va='top',transform=legend.transAxes)
legend.text(0,.73,'Cell colour = respondents (%)',fontsize=13,transform=legend.transAxes)
cbax=legend.inset_axes([0,.52,.94,.09]);cb=fig.colorbar(im,cax=cbax,orientation='horizontal',ticks=[0,15,30,45]);cb.outline.set_visible(False);cb.ax.tick_params(labelsize=12)
legend.add_patch(Rectangle((0,.28),.13,.13,fill=False,ec=RED,lw=2.3,transform=legend.transAxes))
legend.text(.19,.345,'Both ratings are 4 or 5',va='center',fontsize=13,transform=legend.transAxes)
legend.text(0,.10,'1 = strongly disagree\n5 = strongly agree',fontsize=13,linespacing=1.35,va='center',transform=legend.transAxes)
fig.subplots_adjust(left=.058,right=.984,top=.88,bottom=.09,wspace=.24,hspace=.48)
finalize_figure(fig,OUT/'fig05_joint_distributions')

print('Saved five figures to', OUT)
