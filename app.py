from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import sqlite3, json, os
from datetime import datetime

ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('KB_DB', str(ROOT/'knowledge.db')))
app=FastAPI(title='个人知识库 API',version='1.0.0')

def conn():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
 with conn() as c:
  c.execute('CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL, tags TEXT NOT NULL DEFAULT "[]", mood TEXT NOT NULL DEFAULT "", created_at TEXT NOT NULL, updated_at TEXT NOT NULL)')
init()
class Entry(BaseModel):
 kind:str=Field(pattern='^(note|daily|task)$')
 title:str=Field(min_length=1,max_length=200)
 content:str=''
 tags:list[str]=Field(default_factory=list)
 mood:str=''
class EntryPatch(BaseModel):
 kind:Optional[str]=Field(default=None,pattern='^(note|daily|task)$')
 title:Optional[str]=Field(default=None,min_length=1,max_length=200)
 content:Optional[str]=None
 tags:Optional[list[str]]=None
 mood:Optional[str]=None

def serialize(r):
 d=dict(r);d['tags']=json.loads(d['tags']);return d
@app.get('/api/entries')
def list_entries(kind:Optional[str]=None,q:str=''):
 sql='SELECT * FROM entries WHERE 1=1';params=[]
 if kind:sql+=' AND kind=?';params.append(kind)
 if q:sql+=' AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)';params.extend([f'%{q}%']*3)
 sql+=' ORDER BY updated_at DESC'
 with conn() as c:return [serialize(r) for r in c.execute(sql,params)]
@app.post('/api/entries',status_code=201)
def create_entry(item:Entry):
 now=datetime.now().astimezone().isoformat(timespec='seconds')
 with conn() as c:
  cur=c.execute('INSERT INTO entries(kind,title,content,tags,mood,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',(item.kind,item.title,item.content,json.dumps(item.tags,ensure_ascii=False),item.mood,now,now))
  return serialize(c.execute('SELECT * FROM entries WHERE id=?',(cur.lastrowid,)).fetchone())
@app.put('/api/entries/{entry_id}')
def update_entry(entry_id:int,patch:EntryPatch):
 with conn() as c:
  row=c.execute('SELECT * FROM entries WHERE id=?',(entry_id,)).fetchone()
  if not row:raise HTTPException(404,'记录不存在')
  old=serialize(row);data=patch.model_dump(exclude_unset=True)
  old.update(data)
  c.execute('UPDATE entries SET kind=?,title=?,content=?,tags=?,mood=?,updated_at=? WHERE id=?',(old['kind'],old['title'],old['content'],json.dumps(old['tags'],ensure_ascii=False),old['mood'],datetime.now().astimezone().isoformat(timespec='seconds'),entry_id))
  return serialize(c.execute('SELECT * FROM entries WHERE id=?',(entry_id,)).fetchone())
@app.delete('/api/entries/{entry_id}')
def delete_entry(entry_id:int):
 with conn() as c:
  result=c.execute('DELETE FROM entries WHERE id=?',(entry_id,))
  if not result.rowcount:raise HTTPException(404,'记录不存在')
 return {'ok':True}
@app.get('/api/export')
def export():return {'entries':list_entries(),'exported_at':datetime.now().astimezone().isoformat()}
@app.post('/api/import')
def import_data(payload:dict):
 items=payload.get('entries',[])
 if not isinstance(items,list) or len(items)>10000:raise HTTPException(400,'无效数据')
 parsed=[Entry.model_validate({k:v for k,v in x.items() if k in Entry.model_fields}) for x in items]
 with conn() as c:
  for item in parsed:
   now=datetime.now().astimezone().isoformat(timespec='seconds')
   c.execute('INSERT INTO entries(kind,title,content,tags,mood,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',(item.kind,item.title,item.content,json.dumps(item.tags,ensure_ascii=False),item.mood,now,now))
 return {'imported':len(parsed)}
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
@app.get('/')
def home():return FileResponse(ROOT/'static'/'index.html')
