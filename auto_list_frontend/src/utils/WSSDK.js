function getSpeedWithAjax(url) {
  return new Promise((resolve, reject) => {
    var oreject=reject;
    var reject=(d)=>{
      console.error(d)
      oreject(d)
    }
    try{
      let start = null;
      let end = null;
      start = new Date().getTime();
      const xhr = new XMLHttpRequest();
      xhr.onloadend
      xhr.onreadystatechange = function () {
        //get the code and status
        var code = xhr.status;
        var allow_status = [200, 304,100,101,201,202,203,204,205,301,302,303,307];
        console.log(code)
          if (xhr.readyState === 4) {
              if(allow_status.indexOf(code)>-1){
                end = new Date().getTime();
                const size = xhr.getResponseHeader('Content-Length') / 1024;
                const speed = size * 1000 / (end - start)
                resolve(speed);
              }else{
                reject()
              }
          }
      }
      xhr.onerror=(e)=>{
        reject(e)
      }
      //catch the xhr instance error and log it
      xhr.onabort=(e)=>{
        reject(e)
      }
      xhr.ontimeout=(e)=>{
        reject(e)
      }
      xhr.open('GET', url, true);
      xhr.send();
    }catch(e){
      console.error(e)
      console.log(e)
      reject(e)
    }
  })
}
function getNetSpeed(url, times=3) {
  // 多次测速求平均值
  var isonline=false;
  var arr = [];
  for (let i = 0; i < times; i++) {
      arr.push(getSpeedWithAjax(url))
  }
  var failed_times=0;
  return Promise.all(arr).then(speeds => {
      // debugger;
      let sum = 0;
      speeds.forEach(speed => {
          sum += speed;
      });
      return [true,sum / times];
  }).catch((errors) => {
    failed_times++;
    if(failed_times>=times){
      return [false,null]
    }
  })
}
class WSSDK {
  constructor({url,ping_data="ping",pong_data="pong",try_times=5,ping_interval=3000,reconnect_delay=1000,check_internet_times=3,check_internet_delay=5000}){
    var pingData="",pongData=""
    //check if data is object
    if(typeof ping_data=='object'){
        pingData=JSON.stringify(ping_data)
    }else{
        pingData=String(ping_data)
    }
    if(typeof pong_data=='object'){
        pongData=JSON.stringify(pong_data)
    }else{
        pongData=String(pong_data)
    }
    this.ping_data=pingData
    this.pong_data=pongData
    this.try_times=try_times
    this.ourl=url
    this.nohead_url=url.replace("wss://","").replace("ws://","")
    this.event_token="-WSSDK?t="+String(Date.now())+"&id="+this.gn_ws_id()
    
    this.url=this.ourl
    //this.url='ws://127.0.0.1:3000/botapi?id='+listenid
    this.timeout=0
    this.recive=false
    this.interval=null
    this.lasttime=Date.now()
    this.reconnect_lock=false
    this.error=false
    
    this.popresult=null
    this.inserttimes=0
    this.i=0
    this.eventsNames=[]
    /*this.tasks=new Proxy([],{
      set:(obj,prop,value)=>{
        obj[prop]=value
        this.middlewarehandler()
        return true;
      }
    })}*/
    this.tasks=[]
    this.usemiddleware=[]
    this.sendobjects={
      chat:this.chat
    }
    this.ping_interval=ping_interval
    this.reconnect_delay=reconnect_delay
    this.reconnect_times=0
    this.check_internet_times=check_internet_times
    this.check_internet_delay=check_internet_delay
    this.check_internet_timeouter=null
    //use localstorage to store the instance_data of the instance
    this.instance_data=null
    if(this.instance_data==null){
      this.oinstance_data={}
      this.oqueue=[]
    }else{
      this.oinstance_data=JSON.parse(this.instance_data)
      this.oqueue=this.instance_data.queue
    }
    this.instance_data=new Proxy(this.oinstance_data,{
      set:(obj,prop,value)=>{
        this.emit('instance_data_change',{prop:prop,value:value})
        obj[prop]=value
        //localStorage.setItem('instance_data',JSON.stringify(obj))
        this.emit('instance_data_saved',{prop:prop,value:value})
        return true;
      },
      get:(obj,prop)=>{
        return obj[prop]
      }
    })
    var __this=this
    this.queue=new Proxy(this.oqueue,{
      get:function(target,key){
        if(key=='length'){
          return target.length
        }
        return target[key]
      },
      set:function(target,key,value){
        if(key=='length'){
          return target.length
        }
        target[key]=value
        this.emit('queue_change',{key:key,value:value})
        this.emit('queue_saving',{key:key,value:value})
        __this.instance_data["queue"]=target
        this.emit('queue_will_be_saved',{key:key,value:value})
        return true
      }
    })
    this.send_handler=(data)=>{
      if(this.reconnect_lock==false && this.ws && this.ws.readyState==1){
        console.log("send origin data "+data)
          //check if data is object
          var senddata=""
          if(typeof data=='object'){
              senddata=JSON.stringify(data)
          }else{
              senddata=String(data)
          }
          console.log("send data:",senddata)
          this.ws.send(senddata)
      }else{
          this.insertqueue(data)
      }
    }
    this.close_handler=()=>{
      if(this.reconnect_lock==false && this.ws && this.ws.readyState==1){
        this.ws.close()
      }
    }
    this.start_handler=()=>{
      this.initws()
    }
    this.on('send',this.send_handler)
    this.on('close',this.close_handler)
    this.on('start',this.start_handler)
    this.initws()
    
  }
  reconnect(){
    if(this.reconnect_lock!=true){
      this.emit("need_reconnect")
      this.reconnect_lock=true
      clearInterval(this.interval)
      this.interval=null
      //console.log(this.popresult!=null)
      
      this.ws.close()
      this.ws=null
      this.emit("reconnecting")
      this.reconnect_times+=1
      
      this.off('send',this.send_handler)
      this.off('close',this.close_handler)
      this.off('start',this.start_handler)
      if(this.reconnect_times>=this.check_internet_times){
        this.reconnect_times=0
        this.check_internet()
      }else{
        console.log('reconnect attached')
        this.emit('in_reconnect')
        setTimeout(()=>{
          
        console.log('reconnect begin')
          this.emit("reconnecting")
          this.initws()
        },this.reconnect_delay)
      }
    }
  }
  initws(){
    this.reconnect_lock=false
    
    try{
      console.log(this.url)
      this.ws=new WebSocket(this.url)
      this.ws.osend=this.ws.send
      this.ws.send=(data)=>{
          //this.recive=false
          if(data==this.ping_data){
              this.emit("onping")
            if(this.ws.readyState==1){
              this.ws.osend(data)
              setTimeout(()=>{
                if(this.recive==false){
                  this.timeout+=1
                  this.emit("ping_failed")
                  if(this.timeout>=this.try_times&&this.error==false){
                    //this.reconnect_lock=false
                    
                    this.reconnect()
                  }
                }
              },500)
            }else if(this.ws.readyState!=0){
              this.timeout+=1
              this.emit("ping_failed")
                  if(this.timeout>=this.try_times&&this.error==false){
                  
                    this.reconnect_lock=false
                    this.reconnect()
                  }
            }
          }else{
            this.ws.osend(data)
          }
      }
      this.ws.onmessage=(msg)=>{
        this.error=false
        this.recive=true
        this.timeout=0
        console.log(msg.data)
        this.msghandler(msg.data)
        this.recive=false
      }
      this.ws.onopen=()=>{
        this.error=false
        //console.log('open')
        this.emit('connect')
        if(this.error==false){
          this.ws.send(this.ping_data)
          this.interval=setInterval(()=>{
              //console.log('hbi')
              if(this.recive==false){
                //console.log('send ping')
                this.ws.send(this.ping_data)
              }
          },this.ping_interval)
          for(var i in this.queue){
            var data=this.popqueue()
            this.emit("send",data)
          }
        }
      }
      this.ws.onerror=(e)=>{
        this.error=true
        console.log(String(e))
        if(String(e).indexOf("SSL routines:ssl3_get_record")!=-1){
          this.emit("changews")
        }
        //console.log('onerror')
        this.emit('error',e)
        this.reconnect()
      }
      /*this.ws.on('close',()=>{
        console.log('send close')
        if(this.reconnect_lock==false){
          this.reconnect()
        }
      })*/
      
    }catch(e){
      this.reconnect()
    }
  }
  emit(name,data="undefined5"){
    console.log('emit event ');
    if(this.eventsNames.indexOf(name)==-1){
        this.eventsNames.push(name)
    }
    window.dispatchEvent(new CustomEvent(name+this.event_token,{detail:data, bubbles: true }));
    console.log("emit event "+name+" done");
  }
  on(name,cb){
    console.log('register event '+name);
    //console.log(this)
    if(this.eventsNames.indexOf(name)==-1){
        this.eventsNames.push(name)
    }
    window.addEventListener(name+this.event_token,(e)=>{
      console.log("event "+name+" received");
      //get the event data
      console.log(e.detail)
      cb(e.detail)
    });
    console.log('register event '+name+' done');
  }
  send(data){
    this.emit('send',data)
  }
  close(){
    this.emit('close')
  }
  popqueue(){
    var result=this.queue[0]
    this.popresult=result
    console.log(this.popresult==null)
    var tmp=[]
    if(this.queue.length<=1){
      this.queue=tmp
    }else{
      for(var i=0;i<this.queue.length-1;i++){
        tmp[i]=this.queue[i+1]
      }
      this.queue=tmp
    }
    //console.log('inpop')
    //console.log(this.queue)
    return result
  }
  insertqueue(data){
    this.inserttimes+=1
    var tmp=[]
    tmp[0]=data
    for(var i=0;i<this.queue.length;i++){
      tmp[1+i]=this.queue[i]
    }
    this.queue=tmp
  }
  msghandler(data){
      if(data!=this.pong_data){
        this.emit('message',data)
      }else{
          this.emit("alive")
      }
  }
  off(evname,cb){
    window.removeEventListener(evname+this.event_token,cb);
  }
  gn_ws_id(){
    //timestamp+random
    
    var random=(Math.random()*Math.random()*Math.random())*(Math.random()*Math.random()*Math.random())*(Math.random()*Math.random()*Math.random())*(new Date().getTime()*new Date().getTime())
    return String(random)
  }
  check_internet(){
    var __this=this
    //generate a random id from 1 to 1853354153
    var song_id=Math.floor(Math.random()*1853354153)
    //listen the network change
    var result=getSpeedWithAjax("https://api.injahow.cn/meting/?type=lrc&id="+song_id)
    result.then(()=>{
      clearTimeout(__this.check_internet_timeouter)
      __this.check_internet_timeouter=null
      this.emit('has_internet')
      this.emit("wakeup")
      this.initws()
    }).catch((e)=>{
      this.emit("no_internet")
      console.log(e)
      var __this=this
      this.emit("sleep")
      this.check_internet_timeouter=setTimeout(()=>{
        __this.check_internet()
      },this.check_internet_delay)
    })
  }
  start(){
    this.emit('start')
  }
}
export default WSSDK

