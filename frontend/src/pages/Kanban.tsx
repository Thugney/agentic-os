import React,{useMemo,useState}from'react';
import{post}from'../api/client';
import{useData}from'../app/hooks';
import{KanbanBoard}from'../components/kanban/KanbanBoard';
import{Badge as UIBadge,Button as UIButton,Card as UICard,SectionHeader as UISectionHeader}from'../components/primitives/Card';
import{EffectiveSettings,KanbanTask,SystemStatus}from'../api/types';

const h=React.createElement;
const CardAny=UICard as any;
const BadgeAny=UIBadge as any;
const ButtonAny=UIButton as any;
const HeaderAny=UISectionHeader as any;
const API=String.fromCharCode(47);

export function Kanban(){
  const{data,error,refresh}=useData<KanbanTask[]>(API+'kanban/tasks');
  const settings=useData<EffectiveSettings>(API+'settings/effective');
  const runtimes=useData<SystemStatus[]>(API+'runtime/adapters',7000);
  const agents=settings.data?.agents||[];
  const workspaces=settings.data?.workspaces||[];
  const capabilities=settings.data?.capabilities||[];
  const[form,setForm]=useState({title:'',description:'',status:'Backlog',priority:'normal',agent:'',workspace:'',capability_id:'',memory_scope:'workspace',schedule:'manual',schedule_intent:'manual',approval_gate:'ask-before-run',approval_state:'needs_approval',validation_command:''});
  const selectedRuntime=useMemo(()=>runtimes.data?.find(r=>r.name===form.agent||r.adapter_key===form.agent),[runtimes.data,form.agent]);
  const allowedCaps=capabilities.filter((c:any)=>!form.agent||c.owning_agent===form.agent||c.owning_agent===selectedRuntime?.adapter_key);
  async function add(){if(!form.title.trim())return;await post(API+'kanban/tasks',form);setForm({...form,title:'',description:''});refresh()}
  function set(k:string,v:string){setForm({...form,[k]:v})}
  return h('div',{className:'page-stack'},
    h(HeaderAny,{eyebrow:'agent work queue',title:'Work Orders'}),
    error?h('p',{className:'error-panel'},error):null,
    h(CardAny,null,
      h('h3',null,'What happens when you create a work order?'),
      h('p',null,'A work order is stored in the backend with runtime, capability, workspace, memory scope, approval state, validation command, and audit trail. It does not run until approved and the runtime adapter is actually ready.'),
      h('div',{className:'chip-row'},h(BadgeAny,null,'backend connected'),h(BadgeAny,null,'approval gated'),h(BadgeAny,null,'runtime probed'),h(BadgeAny,null,'audit logged'))
    ),
    h(CardAny,{className:'run-form'},
      h('h3',null,'Create work order'),
      h('label',null,'Title',h('input',{value:form.title,onChange:(e:any)=>set('title',e.target.value),placeholder:'Build a safe Codex change or ask DeepSeek to research'})),
      h('label',null,'Description',h('textarea',{value:form.description,onChange:(e:any)=>set('description',e.target.value),placeholder:'Task intent, expected output, constraints, files/context to use.'})),
      h('div',{className:'summary-grid'},
        h('label',null,'Agent/runtime',h('select',{value:form.agent,onChange:(e:any)=>set('agent',e.target.value)},h('option',{value:''},'choose runtime'),agents.map((a:any)=>h('option',{key:a.name,value:a.name},a.label||a.name)))),
        h('label',null,'Workspace',h('select',{value:form.workspace,onChange:(e:any)=>set('workspace',e.target.value)},h('option',{value:''},'none'),workspaces.map((w:any)=>h('option',{key:w.name,value:w.name},w.name)))),
        h('label',null,'Capability',h('select',{value:form.capability_id,onChange:(e:any)=>set('capability_id',e.target.value)},h('option',{value:''},'none'),allowedCaps.map((c:any)=>h('option',{key:c.id||c.name,value:c.id||c.name},c.name||c.id)))),
        h('label',null,'Memory scope',h('select',{value:form.memory_scope,onChange:(e:any)=>set('memory_scope',e.target.value)},['none','session','workspace','project','global'].map(v=>h('option',{key:v},v))))
      ),
      selectedRuntime?h('div',{className:'runtime-mini'},h('strong',null,selectedRuntime.ready?'Runtime ready':'Runtime blocked'),h('span',null,selectedRuntime.detail||selectedRuntime.status)):null,
      h('div',{className:'summary-grid'},
        h('label',null,'Priority',h('select',{value:form.priority,onChange:(e:any)=>set('priority',e.target.value)},['low','normal','high','urgent'].map(v=>h('option',{key:v},v)))),
        h('label',null,'Schedule intent',h('select',{value:form.schedule_intent,onChange:(e:any)=>setForm({...form,schedule:e.target.value,schedule_intent:e.target.value})},['manual','run-once-after-approval','recurring-later'].map(v=>h('option',{key:v},v)))),
        h('label',null,'Approval gate',h('select',{value:form.approval_gate,onChange:(e:any)=>set('approval_gate',e.target.value)},['ask-before-run','ask-before-file-write','ask-before-deploy','manual-only'].map(v=>h('option',{key:v},v)))),
        h('label',null,'Validation command',h('input',{value:form.validation_command,onChange:(e:any)=>set('validation_command',e.target.value),placeholder:'npm --prefix frontend run build'}))
      ),
      h(ButtonAny,{onClick:add},'Create backend work order')
    ),
    h(KanbanBoard,{tasks:data||[],onChanged:refresh})
  )
}
