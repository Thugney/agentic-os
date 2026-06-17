const API='/api';

export function getToken(){return localStorage.getItem('agentic_token')||''}
export function setToken(token:string){localStorage.setItem('agentic_token',token)}

export async function api<T>(path:string, opts:RequestInit={}):Promise<T>{
  const token=getToken();
  const headers:Record<string,string>={'Content-Type':'application/json', ...((opts.headers as Record<string,string>)||{})};
  if(token) headers['x-admin-token']=token;
  const res=await fetch(API+path,{...opts,headers});
  if(!res.ok){
    const text=await res.text();
    throw new Error(text||`${res.status} ${res.statusText}`);
  }
  const type=res.headers.get('content-type')||'';
  if(type.includes('application/json')) return res.json();
  return (await res.text()) as T;
}
export const get=<T=any>(p:string)=>api<T>(p);
export const post=<T=any>(p:string,b:any)=>api<T>(p,{method:'POST',body:JSON.stringify(b)});
export const patch=<T=any>(p:string,b:any)=>api<T>(p,{method:'PATCH',body:JSON.stringify(b)});
