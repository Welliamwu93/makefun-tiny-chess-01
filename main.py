# tiny-chess-01: fixed-depth alpha-beta, material + piece-square eval, stdlib only.
import json,os,sys,urllib.request as U
E=os.environ["MAKEFUN_ENV_URL"]
V={"p":100,"n":320,"b":330,"r":500,"q":900,"k":20000}
INF=10**7;MATE=10**6
def post(p,b):
    r=U.Request(E+p,json.dumps(b).encode(),{"content-type":"application/json"})
    try:return json.load(U.urlopen(r))
    except U.HTTPError as x:sys.exit(f"{p}: {x.code} {x.read()}")
def sq(s):return (8-int(s[1]))*8+ord(s[0])-97
KN=[[(r+a,c+b) for a,b in((1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)) if 0<=r+a<8 and 0<=c+b<8] for r in range(8) for c in range(8)]
KG=[[(r+a,c+b) for a in(-1,0,1) for b in(-1,0,1) if (a or b) and 0<=r+a<8 and 0<=c+b<8] for r in range(8) for c in range(8)]
DIRS={"b":[(1,1),(1,-1),(-1,1),(-1,-1)],"r":[(1,0),(-1,0),(0,1),(0,-1)]}
DIRS["q"]=DIRS["b"]+DIRS["r"]
def ray(i,dirs):
    out=[];r,c=divmod(i,8)
    for a,b in dirs:
        x,y=r+a,c+b;ray_=[]
        while 0<=x<8 and 0<=y<8:ray_.append(x*8+y);x+=a;y+=b
        out.append(ray_)
    return out
def gen(b,w):
    me=str.isupper if w else str.islower;M=[]
    for i,p in enumerate(b):
        if p=="." or not me(p):continue
        t=p.lower();r,c=divmod(i,8)
        if t=="p":
            d=-1 if w else 1;f=i+8*d
            if 0<=f<64 and b[f]==".":
                M.append((i,f))
                if (r==(6 if w else 1)) and b[f+8*d]==".":M.append((i,f+8*d))
            for dc in(-1,1):
                if 0<=c+dc<8 and 0<=r+d<8:
                    g=(r+d)*8+c+dc
                    if b[g]!="." and not me(b[g]):M.append((i,g))
        elif t in"nk":
            for g in(KN if t=="n" else KG)[i]:
                j=g[0]*8+g[1]
                if b[j]=="." or not me(b[j]):M.append((i,j))
        else:
            for ry in ray(i,DIRS[t]):
                for j in ry:
                    if b[j]=="." :M.append((i,j))
                    else:
                        if not me(b[j]):M.append((i,j))
                        break
    return [(f,t,"") for f,t in M]
def make(b,m,w):
    f,t,pr=m;b=list(b);p=b[f];b[f]="."
    if p.lower()=="p" and abs(f-t)%8 and b[t]=="." :b[t+(8 if w else -8)]="."
    if p.lower()=="k" and abs(f-t)==2:
        rf,rt=(7,5) if t>f else(0,3);base=(56 if w else 0)
        b[base+rt]=b[base+rf];b[base+rf]="."
    if p.lower()=="p" and (t<8 or t>=56):p="Q" if w else "q"
    b[t]=p;return "".join(b)
def ev(b):
    s=0
    for i,p in enumerate(b):
        if p!=".":
            r,c=divmod(i,8);t=p.lower();w=p.isupper();v=V[t]
            k=int(7-abs(2*r-7)/2-abs(2*c-7)/2)
            if t=="p":v+=(6-r if w else r-1)*3+k*2
            elif t=="n":v+=k*5
            elif t in"bq":v+=k*2
            elif t=="k":v+=25 if (r==(7 if w else 0) and c in(1,6)) else 0
            s+=v if w else -v
    return s
def qs(b,w,a,z):
    s=ev(b) if w else -ev(b)
    if s>=z:return s
    a=max(a,s)
    for m in sorted([m for m in gen(b,w) if b[m[1]]!="."],key=lambda m:-V[b[m[1]].lower()]):
        v=-qs(make(b,m,w),not w,-z,-a)
        if v>=z:return v
        a=max(a,v)
    return a
def ns(b,w,d,a,z,ply):
    if ("K" if w else "k") not in b:return -MATE+ply
    if d==0:return qs(b,w,a,z)
    best=-INF
    M=sorted(gen(b,w),key=lambda m:-(V[b[m[1]].lower()] if b[m[1]]!="." else 0))
    for m in M:
        v=-ns(make(b,m,w),not w,d-1,-z,-a,ply+1)
        best=max(best,v);a=max(a,v)
        if a>=z:break
    return best if M else 0
def choose(fen,legal):
    f=fen.split();b=""
    for row in f[0].split("/"):
        for c in row:b+="."*int(c) if c.isdigit() else c
    w=f[1]=="w";best=None;bs=-INF
    for u in legal:
        nb=make(b,(sq(u[:2]),sq(u[2:4]),u[4:]),w)
        s=-ns(nb,not w,DEPTH-1,-INF,-bs,1)
        if best is None or s>bs:best,bs=u,s
    return best
DEPTH=4
while True:
    g=post("/game",{})
    if g["status"]=="done":break
    while g["status"]=="your_move":
        g=post("/move",{"game":g["game"],"move":choose(g["fen"],g["legal_moves"])})
    print(g["game"],g["outcome"],g["reason"],file=sys.stderr)
