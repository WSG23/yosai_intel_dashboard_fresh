type Tab = "dashboard"|"analytics"|"graphs"|"export"|"upload"|"settings";
export default function Nav({ tab, onSelect, onLogout }:{
  tab: Tab; onSelect:(t:Tab)=>void; onLogout:()=>void;
}) {
  const item = (id:Tab, label:string) => (
    <button
      key={id}
      onClick={()=>onSelect(id)}
      className={"px-3 py-2 rounded-md text-sm font-medium " + (tab===id ? "bg-gray-900 text-white" : "text-gray-300 hover:bg-gray-700 hover:text-white")}
      style={{marginRight:8}}
    >
      {label}
    </button>
  );
  return (
    <nav className="bg-gray-800" style={{padding:12, display:"flex", alignItems:"center"}}>
      <div className="text-white font-semibold" style={{marginRight:12}}>Yōsai Intel</div>
      {item("dashboard","Dashboard")}
      {item("analytics","Analytics")}
      {item("graphs","Graphs")}
      {item("export","Export")}
      {item("upload","Upload")}
      {item("settings","Settings")}
      <div style={{flex:1}} />
      <button onClick={onLogout} className="px-3 py-2 rounded-md text-sm font-medium bg-red-600 text-white">Logout</button>
    </nav>
  );
}
