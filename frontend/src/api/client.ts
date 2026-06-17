const API='/api';
export async function api<T>(path:string, opts:RequestInit={}):Promise<T>{
  const token=localStorage.getItem('agentic_token')||'';
  const headers:any={'Content-Type':'application/json', ...(opts.headers||{})};
  if(token) headers['x-admin-token']=token;
  const res=await fetch(API+path,{...opts,headers});
  if(!res.ok) throw new Error(await res.text());
  return res.json();
}
export const get=(p:string)=>api<any>(p);
export const post=(p:string,b:any)=>api<any>(p,{method:'POST',body:JSON.stringify(b)});
export const patch=(p:string,b:any)=>api<any>(p,{method:'PATCH',body:JSON.stringify(b)});
