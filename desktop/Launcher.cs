using System;
using System.IO;
using System.Net;
using System.Diagnostics;
using System.Threading;
using System.Windows.Forms;
using System.Web.Script.Serialization;
using System.Collections.Generic;
class Launcher {
 static bool Ready(string url) {
  try {var r=(HttpWebRequest)WebRequest.Create(url+"/health");r.Proxy=null;r.Timeout=1200;using(var response=r.GetResponse())using(var reader=new StreamReader(response.GetResponseStream()))return reader.ReadToEnd().Contains("IMG2GILB");} catch{return false;}
 }
 [STAThread] static void Main() {
  string root=AppDomain.CurrentDomain.BaseDirectory;
  try {
   var c=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(File.ReadAllText(Path.Combine(root,"runtime.json")));
   string url="http://127.0.0.1:"+c["port"].ToString();
   bool created;using(var mutex=new Mutex(true,"Local\\IMG2GILB_Launcher",out created)) {
    if(!Ready(url) && created) {
     var p=new ProcessStartInfo(c["python"].ToString(),"\""+Path.Combine(root,"service.py")+"\"");p.WorkingDirectory=root;p.UseShellExecute=false;p.CreateNoWindow=true;p.WindowStyle=ProcessWindowStyle.Hidden;Process.Start(p);
    }
    for(int i=0;i<60&&!Ready(url);i++)Thread.Sleep(500);
    if(!Ready(url))throw new Exception("Der lokale Dienst wurde nicht bereit. Bitte service.log im App-Ordner prüfen.");
    Process.Start(new ProcessStartInfo(url){UseShellExecute=true});
   }
  } catch(Exception e) { File.AppendAllText(Path.Combine(root,"launcher.log"),DateTime.Now+" "+e+Environment.NewLine);MessageBox.Show(e.Message,"IMG2GILB konnte nicht starten",MessageBoxButtons.OK,MessageBoxIcon.Error);}
 }
}
