// JavaScript Document
var imgPath="";
var ajaxPath="ajaxload";
function getRnd(){
	return String((new Date()).getTime()).replace(/\D/gi,'');
}
function GetRandom(min,max){//生成随机数
	if(min>max){return(-1);}
	if(min==max){return(min);}
	return(min+parseInt(Math.random()*(max-min+1)));
}

window.AeroDialog = {
	//自适应最小宽度
	minWidth : 333,
	//自适应最大宽度,auto
	maxWidth : 333,
	//模态层
	Cover : {
		//透明度
		opacity : 0.7,
		//背景颜色
		background : '#DCE2F1'
	},
	//动画效果
	Flash : false,
	//动画效果
	WinAnimation : {
		Speed:500,//效果延迟时间,单位是毫秒
		FlashMode:'easeOutCubic'//特效方式
	},
	//按钮文本
	Btntxt : {
		//action 值 ok
		OK     : '确 定',
		//action 值 no
		NO     : ' 否 ',
		//action 值 yes
		YES    : ' 是 ',
		//action 值 cancel
		CANCEL : '取 消',
		//action 值 CLOSE
		CLOSE  : '关闭'
	}
};

window.AeroWindow = {
	ShowDesktop:true,
	ShowTaskbar:true,
	TaskbarSite:'bottom',//设置任务栏位置
	ShowStartMenu:true,
	WinZIndex:1000,
	AllowFlash:true
};

(function($){
   	var AeroWindowPlugin=function(element,options){//插件定义
		this.id=element.id;//获取ID名称
		var elem=$(element);
		var obj=this;
		var opt=$.extend({
			WinTitle:'AeroWindow',//标题
			WinIconFile:'images/Icons/default.png',//默认窗口左上角图标
			WinIcon:true,//在桌面显示图标,在显示任何窗体的时候
			WinDraggable:true,//拖动窗体
			WinStatus:'window',//窗体状态,maximized,minimized
			WinResizable:true,//是否可以改变窗口大小
			
			FlashSpeed:300,//效果延迟时间,单位是毫秒
			FlashMode:'easeInOutQuart',//特效方式
			TransparentSpeed:300,//透明效果时间
			
			WinPTop:200,//{center/值}初始时离桌面最上边位置
			WinPLeft:100,//{center/值}初始时离桌面最左边位置
			
			OuterWidth:300,//{atuo/值}内宽
			OuterHeight:200,//{atuo/值}内高
			MinWidth:200,//最小时的宽度
			MinHeight:200,
			WinBWidth:22,
			WinBHeight:52,
			WinBtn : {
				Minimize:true,//显示最小化按钮
				Maximize:true,//显示最大化按钮
				Closable:true//显示关闭按钮
			},
			LoadiFrame:true,//是否允许加载iframe链接内容
			WinElemID:this.id,//指定窗体ID
			WinBMouseCursor:25,//鼠标指针宽度
			TaskbarHeight:40,
			TaskbarSite:aw.TaskbarSite,
			callback:$.noop
		},options||{});//可扩展
		
		var titles='<img src="'+opt.WinIconFile+'" align="absmiddle"><span>'+opt.WinTitle+'</span>';
		var SourceContent=$(elem).html();
		var aeroContent='<div class="tb-mm-content" style="width:'+(opt.OuterWidth-opt.WinBWidth)+'px;height:'+(opt.OuterHeight-opt.WinBHeight)+'px;">'+SourceContent+'</div>';
		
		var WinContainer=$(elem);
		if(aw.showDesktop||aw.ShowTaskbar){//只有显示桌面图标才能缓存窗体
			WinContainer.html(MainAeroWindow(titles,AddWinBtn(opt.WinBtn,this.id),aeroContent));}
		
		WinContainer.css({
		  'z-index':aw.WinZIndex,
		  width:opt.OuterWidth+'px',
		  height:opt.OuterHeight+'px',
		  top:opt.WinPTop+'px',
		  left:opt.WinPLeft+'px',
		  position:'absolute'});
		var aWin=$(elem).find(".AeroWindow"),
		WinContent=$(elem).find(".tb-mm-content"),
		WinContContainer=$(elem).find(".tb-mm-container"),
		BTNSpread=$(elem).find('.winbtn-spread'),
		BTNMin=$(elem).find(".win-minbtn"),
		BTNMax=$(elem).find(".win-maxbtn"),
		BTNRes=$(elem).find(".win-regbtn"),
		BTNClose=$(elem).find(".win-closebtn"),
		taskbar=$('#Taskbar'+this.id);
		BTNRes.css('display','none');
		WinContainer.addClass("AeroWinContainer");
		
		if(WinContainer.find('iframe').length>0)
		{
			WinContent.addClass('loading');
			WinContent.find('iframe').css('visibility','hidden');
			WinContent.append('<div class="iframeHelper"></div>');
			WinContainer.find('iframe').attr({src:$(elem).find('iframe').attr('src')});			
			WinContent.find('iframe').load(function(){
					WinContent.find('iframe').css('visibility','visible');})
		}
			   //获取窗口的最大优先级
	   this.getWinMaxZIndex=function(){
	   	  if(($('body').data('AeroWinMaxZIndex'))==null){
			  $('body').data('AeroWinMaxZIndex',WinContainer.css('z-index'));
		  }
		  i=$('body').data('AeroWinMaxZIndex');
		  i++;
		  WinContainer.css('z-index',i);
		  $('body').data('AeroWinMaxZIndex',WinContainer.css('z-index'));
	   };
		opt.sprChange=!1;
		if(opt.WinDraggable){
		  WinContainer.draggable({//拖拽窗口
			distance:3,
			cancel:'.tb-mm-content',
			//helper:'clone',
			opacity:0.6,
			cursor: 'move',
			start:function(){
			    if((opt.WinStatus=='maximized'||'minimized')&&opt.sprChange==!1){
					obj.ResizeWindow('restoreToMouse');
			    }
				obj.WindowFocus();//设置拖动窗体为焦点
				obj.getWinMaxZIndex();//设置改变大小窗口的优先级
			    aWin.find('.iframeHelper').css({'display':'block'});
				WinContainer.find('iframe').css('visibility','hidden');
			},
			drag:function(){
				WinTop=-1*$(this).offset().top;
				WinLeft=-1*$(this).offset().left;
				aWin.css({backgroundPosition:WinLeft+'px '+WinTop+'px'});
			},
			stop:function(){
			    aWin.find('.iframeHelper').css({'display':'none'});
				WinContainer.draggable({cursorAt:null});
				WinContainer.find('iframe').css('visibility','visible');
			}
		 });
		}
	   
		//设置活动窗口为焦点窗口
	  this.WindowFocus=function(){
		  $(".AeroWindow").removeClass('active');
		  $(".AeroWindow").find('.iframeHelper').css({'display':'block'});
		  aWin.find('.iframeHelper').css({'display':'none'});
		  aWin.addClass('active');
		  $("#Taskbar .Taskbar-Item").removeClass('active');
		  $('#Taskbar'+this.id).addClass('active');
		  WinContainer.css('display','block');
		  $('#Taskbar'+this.id).css({display:'block'});
	  }
	  
	  if(opt.WinResizable){
		WinContainer.resizable({
			minHeight:opt.MinHeight,
			minWidth:opt.MinWidth,
			alsoResize:WinContent,
			handles:'n, e, s, w, ne, se, sw, nw',
			start:function(){
				/*WinContContainer.css('visibility','visible');*/
				aWin.find('.iframeHelper').css({'display':'block'});
				$(".AeroWindow").removeClass('active');
				aWin.addClass('active');
				obj.getWinMaxZIndex();//设置改变大小窗口的优先级
			},
			stop:function(){
				aWin.find('.iframeHelper').css({'display':'none'});
			}
		 });
	   }
	   
		var getCurrentWinSize=function(){
		  height=$(elem).height();
		  width=$(elem).width();
		};
		
		//保存改变大小后窗口的位置
		var saveWinSize=function(){
			opt.OuterHeight=WinContainer.height();
			opt.OuterWidth=WinContainer.width();
			opt.WinTop=WinContainer.offset().top;
			opt.WinLeft=WinContainer.offset().left;
		};
		this.get=function(key){return(opt[key]);}
		this.set=function(key,value){opt[key]=value;}
		/*this.RefreshIframeURL=function(){
			if(WinContainer.find('iframe').length>0){
				WinContainer.find('iframe').attr({src:$(elem).find('iframe').attr('src')});
			}
		}*/
		
	  //桌面ICON设置
	  this.DesktopIconHandler=function(){
		$('#DesktopIcons .DesktopIconContainer').live("mouseover mouseout",function(event){//鼠标经过桌面图标时
			if(event.type=='mouseover'){
				if($(this).hasClass('mouseout'))
					$(this).removeClass('mouseout');
				$(this).addClass('mouseover');
			}
			else{
				$(this).removeClass('mouseover');
				if($(this).hasClass('mouseclicked'))
					$(this).addClass('mouseout');
			}
		});
		
		/*$('#DesktopIcon'+this.id).live("click",function(){//单击桌面图标时
			$('#DesktopIcons .DesktopIconContainer').removeClass('mouseclicked');
			$('#DesktopIcons .DesktopIconContainer').removeClass('mouseout');
			$(this).addClass('mouseclicked');
		});*/
		
	   // $('#DesktopIcon'+this.id).dblclick(function(e){//双击桌面图标时
	    $('#DesktopIcon'+this.id).click(function(e){//单击桌面图标时
			if(opt.WinStatus=='minimized'){obj.ResizeWindow('restore');}
			else if(opt.WinStatus=='window'){obj.WindowFocus();}
			else if(opt.WinStatus=='closed'){
				if(opt.WinURL&&$("#"+obj.id+"-iframe")!==undefined){
					$("#"+obj.id).find('.tb-mm-content').addClass('loading');
					$("#"+obj.id+"-iframe").css("visibility","hidden");
					window.setTimeout(function(){
						$("#"+obj.id+"-iframe").css("display","none").attr("src",opt.WinURL);
						$("#"+obj.id+"-iframe").load(function(){
							$("#"+obj.id).find('.tb-mm-content').removeClass('loading');
							$(this).css("display","block");});},2000);
			     }
			BTNSpread.css('display','none');
			StartOuterWidth=200;
			StartOuterHeight=100;
			EndOuterWidth=200;
			EndOuterHeight=100;
			opt.WinTop=e.pageY-(StartOuterHeight/2);
			opt.WinLeft=e.pageX-(StartOuterWidth/2);
			opt.OuterWidth=StartOuterWidth;
			opt.OuterHeight=StartOuterHeight;
			obj.ResizeWindow('changeFast');
			obj.ResizeWindow('restore');
			opt.WinStatus='onChange';
			opt.OuterWidth=EndOuterWidth;
			opt.OuterHeight=EndOuterHeight;
			opt.WinTop=($(window).height()/2)-(opt.OuterHeight/2);
			opt.WinLeft=($(window).width()/2)-(opt.OuterWidth/2);
			obj.ResizeWindow('changeSize');
			opt.WinStatus='onChange';
			EndOuterWidth=700;
			EndOuterHeight=400;
			MinSpacing=20;
			if((($(window).width()-MinSpacing)<EndOuterWidth)||(($(window).height()-MinSpacing)<EndOuterHeight)){
				a=$(window).width()+MinSpacing-EndOuterWidth;
				b=$(window).height()+MinSpacing-EndOuterHeight;
				if(a<b){
					OuterWidth=$(window).width()-MinSpacing;
					OuterHeight=(EndOuterHeight/(EndOuterWidth/($(window).width())))-MinSpacing;}
				else{
					OuterWidth=(EndOuterWidth/(EndOuterHeight/($(window).height())))-MinSpacing;
					OuterHeight=$(window).height()-MinSpacing;}
				EndOuterWidth=OuterWidth;
				EndOuterHeight=OuterHeight;
			}
			opt.OuterWidth=EndOuterWidth;
			opt.OuterHeight=EndOuterHeight;
			opt.WinTop=($(window).height()/2)-(opt.OuterHeight/2)+GetRandom(-50,50);
			opt.WinLeft=($(window).width()/2)-(opt.OuterWidth/2)+GetRandom(-50,50);
			obj.ResizeWindow('changeSize');
			BTNSpread.css('display','block');
			//$('#Taskbar'+element.id).clone(true).appendTo("#Taskbar");
			//$('#Taskbar'+element.id).remove();
			}
		  });
	   }
	   
	  //任务栏设置
	  this.TaskbarHandler=function(){
		  $('#Taskbar'+this.id).live("mouseover mouseout",function(event){
			  if(event.type=='mouseover')
				  $(this).addClass('hover');
			  else
				  $(this).removeClass('hover');
		  });
		  $('#Taskbar'+this.id).mousedown(function(){
			  $(this).find('img').css({marginTop:'2px',marginLeft:'2px'});
		  });
		  $('#Taskbar'+this.id).mouseup(function(){
			  $(this).find('img').css({marginTop:'0px',marginLeft:'0px'});
		  });
		  $('#Taskbar'+this.id).live("click",function(){//obj.WindowFocus();obj.getWinMaxZIndex();
			  if(opt.WinStatus=='minimized'){
				  if(opt.WinStatusBefore=='maximized'){
					  obj.ResizeWindow('maximize');}
				  else{obj.ResizeWindow('restore');}
			  }
			  else if(opt.WinStatus=='window'||opt.WinStatus=='maximized'){
				  if($('#'+obj.id).find('.AeroWindow').hasClass('active')){
					  obj.ResizeWindow('minimize');}
				  else{obj.WindowFocus();obj.getWinMaxZIndex();}
			  }
		  });
	   }
	   
	   var anim={queue:true,duration:opt.FlashSpeed,easing:opt.FlashMode};
	   this.ResizeWindow=function(NewSize,WindowFocus,WinStatusBefore){
		   var cWidth=opt.OuterWidth-opt.WinBWidth,cHeight=opt.OuterHeight-opt.WinBHeight;
			if(opt.WinStatus=='window'){saveWinSize();}
			opt.WinStatusBefore=opt.WinStatus;//设置为之前状态
			if(WindowFocus===undefined){WindowFocus=true;}
		    if(WindowFocus){obj.WindowFocus();obj.getWinMaxZIndex();}
			switch(NewSize)
			{
				case 'transparent-on':WinContContainer.animate({opacity:0.0},{queue:false,duration:opt.TransparentSpeed});break;
				case 'transparent-off':WinContContainer.animate({opacity:1.0},{queue:false,duration:opt.TransparentSpeed});break;
				case 'maximize':
				BTNSpread.css('display','block');
				BTNMin.css('display','block');
				BTNRes.css('display','block');
				BTNMax.css('display','none');
				/*if(opt.sprChange==!0)
					opt.OuterWidth=opt.sw,opt.OuterHeight=opt.sh;*/
				if(WinContent.css('visibility')=='hidden')
			    {WinContent.css({'visibility':'visible'});}
				if($.browser.msie){}//IE do nothing
				else{aWin.animate({opacity:'fast'},anim);}
				WinContainer.draggable({disabled:true});
				WinContainer.animate({width:$(window).width(),height:(aw.ShowTaskbar?$(window).height()-opt.TaskbarHeight:$(window).height()),
				  top:$(window).scrollTop(),
				  left:$(window).scrollLeft()},{duration:opt.FlashSpeed,easing:opt.FlashMode});
				WinContent.animate({'opacity':1,
				  width:$(window).width()-opt.WinBWidth,
				  height:(aw.ShowTaskbar?$(window).height()-opt.WinBHeight-opt.TaskbarHeight:$(window).height()-opt.WinBHeight)},{queue:true,duration:opt.FlashSpeed,easing:opt.FlashMode,
				  complete:function(){
					WinContainer.resizable({disabled:true});           
					WinContainer.draggable({disabled:false});
				  }
			   });
			   WinContainer.draggable({
				cursorAt:{cursor:"crosshair",top:opt.WinBMouseCursor,left:(opt.OuterWidth/2)}});
			   opt.WinStatus='maximized';
			   break;
			   
			 case 'minimize':
			  $('#Taskbar'+this.id).removeClass('active');
			  BTNSpread.css('display','none');
			  BTNMin.css('display','none');
			  BTNRes.css('display','none');
			  BTNMax.css('display','block');
			  opt.WinStatus='minimized';
			  if($.browser.msie){}
			  else{aWin.animate({opacity:'hide'},anim);}
			  WinContainer.animate({width:opt.MinWidth,height:opt.MinHeight,
				top:-100+$('#Taskbar'+this.id).offset().top,left:$('#Taskbar'+this.id).offset().left},{queue:true,duration:opt.FlashSpeed,easing:opt.FlashMode,complete:function(){WinContainer.css('display','none');}});
			  WinContent.animate({
				  width:opt.MinWidth-opt.WinBWidth,height:opt.MinHeight-opt.WinBHeight},anim);
			  WinContainer.draggable({
				  cursorAt:{cursor:"crosshair",top:opt.WinBMouseCursor,left:(opt.OuterWidth/2)}
			  });
			  WinContainer.resizable('disable');
			  break;
			  
			 case 'restore'://还原窗口
			  BTNSpread.css('display','block');
			  BTNMin.css('display','block');
			  BTNRes.css('display','none');
			  BTNMax.css('display','block');
			  opt.WinStatus='window';
			  WinContainer.css('display','block');
			  aWin.animate({opacity:'show'},anim);
			  if($.browser.msie){
				WinContainer.animate({width:opt.OuterWidth,height:opt.OuterHeight,
					top:opt.WinTop+$(window).scrollTop(),
					left:opt.WinLeft+$(window).scrollLeft()},anim);}
			  else{
				WinContainer.animate({opacity:1,width:opt.OuterWidth,height:opt.OuterHeight,top:opt.WinTop,left:opt.WinLeft},anim);}
			  WinContent.animate({opacity:1,width:cWidth,height:cHeight},anim);
			  WinContainer.draggable({cursorAt:null});
			  WinContainer.resizable('enable');break;
				
				case 'close'://关闭窗口
				  if(WinStatusBefore===undefined){opt.WinStatusBefore=opt.WinStatus;}
				  else{opt.WinStatusBefore=WinStatusBefore;}
				  if($.browser.msie){WinContainer.css('display','none');}
				  else{WinContainer.animate({opacity:0},{queue:true,duration:opt.FlashSpeed,easing:opt.FlashMode,complete:function(){WinContainer.css('display','none');}});}
				  $('#Taskbar'+this.id).css({display:'none'});
				  opt.WinStatus='closed';break;
				 
				case 'changeFast'://点击图标开发窗口并移动到中间
				  WinContainer.css({width:opt.OuterWidth,height:opt.OuterHeight,
					top:opt.WinTop+$(window).scrollTop(),
					left:opt.WinLeft+$(window).scrollLeft()},{});
			      WinContent.css({
					width:cWidth,
					height:cHeight},{});break;
				
				case 'changeSize'://打开窗口从中间到window状态
				  opt.WinStatus='window';
				  WinContent.find('iframe').css('display','none');
				  aWin.animate({opacity:'show'},{queue:true,duration:opt.FlashSpeed,easing:opt.FlashMode});
				  WinContainer.animate({width:opt.OuterWidth,height:opt.OuterHeight,
					  top:opt.WinTop+$(window).scrollTop(),
					  left:opt.WinLeft+$(window).scrollLeft()},anim);
				  WinContent.animate({width:cWidth,height:cHeight},anim);
				  WinContent.find('iframe').animate({opacity:'show'},{queue:true,duration:1000});break; 
				
				case 'restoreToMouse'://在窗口最大化时拖动窗口还原到window状态
				  BTNMin.css('display','block');
				  BTNRes.css('display','none');
				  BTNMax.css('display','block');
				  BTNSpread.css('display','block');
				  WinContainer.css({width:opt.OuterWidth,height:opt.OuterHeight});
				  WinContent.css({width:opt.OuterWidth-opt.WinBWidth,height:opt.OuterHeight-opt.WinBHeight});
				  if(opt.WinStatus!='spreaded')
				  WinContainer.resizable('enable');opt.WinStatus='window';break;
				  
				case 'spread':
				BTNSpread.css('display','block');
				BTNRes.css('display','none');
				BTNMax.css('display','block');
				obj.WindowFocus();obj.getWinMaxZIndex();
				if(WinContent.css('visibility')=='visible')
				{	opt.sw=opt.OuterWidth,opt.sh=opt.OuterHeight,opt.sprChange=!0,opt.WinStatus='spreaded';
					BTNMin.css('display','none');
					WinContent.animate({height:'0px',width:(opt.MinWidth-opt.WinBWidth),opacity:0},{queue:true,duration:opt.FlashSpeed,easing:opt.FlashMode,complete:function(){WinContent.css('visibility','hidden');BTNSpread.removeClass('up');BTNSpread.addClass('down');
					}});
					WinContainer.animate({height:opt.WinBHeight,width:opt.MinWidth},{queue:true,duration:opt.FlashSpeed,complete:function(){
						if(WinContainer.offset().left<0){WinContainer.animate({left:'0px'},200);}
					WinContainer.resizable('disable');}});
				}
				else{opt.sprChange=!1,opt.WinStatus='window';BTNMin.css('display','block');
				WinContent.css('visibility','visible');
					WinContainer.animate({height:opt.sh,width:opt.sw},{duration:opt.FlashSpeed,easing:opt.FlashMode});
					WinContent.animate({height:opt.sh-opt.WinBHeight,width:opt.sw-opt.WinBWidth,opacity:1},{duration:opt.FlashSpeed,easing:opt.FlashMode,complete:function(){WinContainer.resizable('enable');BTNSpread.removeClass('down');BTNSpread.addClass('up');}});
			   }break;
			   default:break;
			}
		}
		
		function initLoad(id){//初始化加载
			if($('#'+id).find('iframe').length>0){
				WinContent.css({overflow:'hidden'});}
			if($('#'+id).next('img').length>0){WinContent.css({overflow:'hidden'});}
			saveWinSize();//初始化窗口位置
			if(aw.ShowTaskbar&&!aw.ShowDesktop){//显示任务栏
				showTaskBarMenu(id,opt);
			}
			if(aw.ShowDesktop){//是否在桌面上创建图标
				ShowDesktopIcon(id,opt);
				showTaskBarMenu(id,opt);
			}
			saveWinSize();
	    };
		
		initLoad(this.id);
		BTNSpread.click(function(){
			obj.ResizeWindow('spread');return(false);
			});
		BTNMin.click(function(){
			obj.ResizeWindow('minimize');return(false);});
		BTNRes.click(function(){
			obj.ResizeWindow('restore');return(false);});
		BTNMax.click(function(){	
			obj.ResizeWindow('maximize');return(false);});
		BTNClose.click(function(){
			obj.ResizeWindow('close');return(false);});
		aWin.click(function(){
			if(!aWin.hasClass('active')){obj.WindowFocus();obj.getWinMaxZIndex();}});
		if(opt.WinBtn.Maximize){
			WinContainer.dblclick(function(){
				switch(opt.WinStatus){
					case'window':obj.ResizeWindow('maximize');break;
					case'maximized':obj.ResizeWindow('restore');break;
					case'minimized':obj.ResizeWindow('restore');break;
					default:break;}});}
		else{
			WinContainer.dblclick(function(){
			  switch(opt.WinStatus){
				  case'maximized':obj.ResizeWindow('restore');break;
				  case'minimized':obj.ResizeWindow('restore');break;
				  default:break;
			  }
			});
		}
		WincallBack(opt,this.id);
	}
	//插件结束
	var aw=AeroWindow;


	
	
	function ShowDesktopIcon(id,set){
		var temp=new Array();
		temp=set.WinTitle.split(' ');
		DesktopIconCaption='';
		$.each(temp,function(index,value){
			if(value.length>17){
				DesktopIconCaption+=value.substr(0,17)+'... ';}
			else{DesktopIconCaption+=value+' ';}
		});
		$('#DesktopIcons').append(
		'<div class="DesktopIconContainer" id="DesktopIcon'+id+'">'+
		'<table cellpadding="0" cellspacing="0" border="0" title="'+set.WinTitle+'">'+
		'<tr>'+
		'	<td class="bg-top"></td>'+
		'</tr>'+
		'<tr>'+
		'	<td class="bg-middle"><img src="'+set.WinIconFile+'" width="58" height="58" border="0"></td>'+
		'</tr>'+
		'<tr>'+
		'	<td class="bg-bg"><p>'+DesktopIconCaption+'</p></td>'+
		'</tr>'+
		'<tr>'+
		'	<td class="bg-bottom"></td>'+
		'</tr>'+
		'</table>'+
	    '</div>');
		$('#DesktopIcon'+id).draggable({
			helper:"original",
			start:function(){
				$('#DesktopIcons .DesktopIconContainer').removeClass('mouseclicked');
				$('#DesktopIcons .DesktopIconContainer').removeClass('mouseout');
				$(this).addClass('mouseclicked');
			}
		});	
	}
	
	function showTaskBarMenu(id,set)
	{
		$('#AeroTaskbar').append(
		'<div id="Taskbar'+id+'" class="Taskbar-Item" title="'+set.WinTitle+'" style="display:none"><img src="'+set.WinIconFile+'"></div>');
	}
	
	function WincallBack(w,id) {//点击最小化，最大化，关闭时回调函数返回值 
        var d, e = aw.WBtns.All;
        $.each(e, function (e, f) {
            $("#" +id+ "_" + f.result).click(function (e) {
                var g = $(this);
                return g.attr("disabled","disabled"),d = w.callback(f.result),g.removeAttr("disabled"),e.preventDefault(),false
            })
        })
    }
	
	$.fn.AeroWindow=function(options){
	  return this.each(function(){
		var element=$(this);
		if(element.data('AeroWindow')) return;
		var AeroWindow=new AeroWindowPlugin(this,options);//为每个新建窗体创建一个对象
		element.data('AeroWindow',AeroWindow);
		AeroWindow.TaskbarHandler();//初始化任务栏
		AeroWindow.DesktopIconHandler();//初始化桌面图标
		if(($('body').data('AeroWindows'))==null){
			$('body').data('AeroWindows',[AeroWindow]);}
		else{$('body').data('AeroWindows').push(AeroWindow);}
	  });
	};
	
	$.fn.AeroWindowLink=function(options){
	  var options=$.extend({
		  WinURL:null,
		  WinTitle:'AeroWindow for jQuery',//标题
		  WinIconFile:'images/Icons/apple.png',//默认窗口左上角图标
		  WinIcon:true,//在桌面显示图标,在显示任何窗体的时候
		  WinDraggable:true,//拖动窗体
		  WinStatus:'window',//窗体状态,maximized,minimized
		  WinResizable:true,//是否可以改变窗口大小
		  
		  FlashSpeed:300,//效果延迟时间,单位是毫秒
		  FlashMode: 'easeInOutBack',//特效方式
		  TransparentSpeed:300,//透明效果时间
		  
		  OuterWidth:300,//{atuo/值}内宽
		  OuterHeight:200,//{atuo/值}内高
		  MinWidth:300,//最小时的宽度
		  MinHeight:200,
		  WinBWidth:22,
		  WinBHeight:52,
		  
		  WinBtn : {
			  Minimize:true,//显示最小化按钮
			  Maximize:true,//显示最大化按钮
			  Closable:true//显示关闭按钮
		  },
		  TaskbarHeight:40,
		  TaskbarSite:aw.TaskbarSite,
		  callback:$.noop
	    },options||{});
	    return this.each(function(){
		  var $this=$(this);
		  var img=$("img",$this).attr("src")?$("img",$this).attr("src"):imgPath+'/icons/default.png';
		  var id="Aerowin-"+getRnd();
		  $('.AeroWindows').append('<div id="'+id+'" style="display: none;">'+'<iframe src="about:blank" width="100%" height="100%" style="display:none; border: 0px;" frameborder="0" id="'+id+'-iframe"></iframe>'+'</div>');
		  options.WinURL=$this.attr("href");
		  options.WinTitle=$this.text();
		  options.WinIconFile=img;
		  options.WinStatus="closed";//初始化窗口状态为关闭
		  $("#"+id).AeroWindow(options);
	   });
	}
	
	function getWinInfo() {//获取窗口值
        var a = document.body,
            b = document.documentElement;
        return {
            x: Math.max(a.scrollWidth, b.clientWidth),
            y: Math.max(a.scrollHeight, b.clientHeight),
            top: Math.max(b.scrollTop, a.scrollTop),
            left: Math.max(b.scrollLeft, a.scrollLeft),
            width: b.clientWidth,
            height: b.clientHeight
        }
    }

	
	//用于回调事件处理
    aw.WBtns = {
	  WMin: [{
		  value: '最小化',
		  result: "wmin"
	  }],
	  WMax: [{
		  value: '最大化',
		  result: "wmax"
	  }],
	  WReg:[{
		  value: '还原',
		  result: 'wreg'
	  }],
	  WClose: [{
		  value: '关闭',
		  result: "wclose"
	  }]
	},
	aw.WBtns.All=aw.WBtns.WMin.concat(aw.WBtns.WMax).concat(aw.WBtns.WReg).concat(aw.WBtns.WClose);
	
   function AddWinBtn(wb,id){//添加窗体控制按钮
	  var b='<a id="'+id+'_spread" href="#" class="winbtn-spread up"></a>';
	  if(wb.Minimize||wb.Maximize||wb.Closable){
	   b+=['<div class="winbtn-leftadge"></div>',wb.Minimize?wb.Maximize||wb.Closable?'<a id="'+id+'_wmin" href="#" class="win-minbtn"></a><div class="winbtn-spacer"></div>':'<a id="'+id+'_wmin" href="#" class="win-minbtn"></a>':"",wb.Maximize?wb.Closable?'<a id="'+id+'_wmax" href="#" class="win-maxbtn"></a><a id="'+id+'_wreg" href="#" class="win-regbtn"></a><div class="winbtn-spacer"></div>':'<a id="'+id+'_wmax" href="#" class="win-maxbtn"></a>':"",wb.Closable?'<a id="'+id+'_wclose" href="#" class="win-closebtn"></a><div class="winbtn-rightedge"></div>':'<div class="winbtn-rightedge"></div>'].join('');}
	   return b.replace(/#/g,'javascript:void(0)');
	}
	
	   /*<iframe  style="position:absolute;z-index:-1;width:100%;height:100%;top:0;left:0;scrolling:no;_width:expression(this.parentNode.offsetWidth);_height:expression(this.parentNode.offsetHeight);opacity:0;filter:alpha(opacity=0)" frameborder="0" src="about:blank"></iframe>*/
   function MainAeroWindow(wTitle,wBtns,wContent)
   {
	  return ['<div class="AeroWindow">',
	  '<table border="0" cellspacing="0" cellpadding="0">',
	  ' <tr>',
	  '   <td class="tb-tl"></td>',
	  '   <td class="tb-tm"></td>',
	  '  <td class="tb-tr"></td>',
		'</tr>',
		'<tr>',
		'  <td class="tb-lm"></td>',
		'  <td class="tb-mm">',
		'  <div class="winTitle"><nobr>',wTitle,'</nobr></div>',
		'  <div class="winBtns">',wBtns,
		'   </div>',
		'   <div class="tb-mm-container">',wContent,
		'   </div>',
		'  </td>',
		'  <td class="tb-rm"></td>',
		'</tr>',
		'<tr>',
		'  <td class="tb-bl"></td>',
		'  <td class="tb-bm"></td>',
		'  <td class="tb-br"></td>',
		'</tr>',
	 '</table>',
	  '</div>'].join('');
   }
	
	
	
	
	//以下为对话框代码
	function divCover(){
		return '<div id="winDialogCover" style="width:100%; height:100%; margin:0px; padding:0px; position:fixed;top:0px; left:0px;  background-color:'+AeroDialog.Cover.background+'; opacity:'+AeroDialog.Cover.opacity+';display:block; "></div>';
	}
	
	function callBack(b) {//button点击，回调函数返回值 
        var d, e = AeroDialog.btn.CLOSE.concat(b.buttons);
        $.each(e, function (e, f) {
            $("#" + b.id + "_" + f.result).click(function (e) {
                var g = $(this);
                return g.attr("disabled","disabled"),d = b.callback(f.result),(typeof d == "undefined" || d) && AeroDialog.close(b.id),g.removeAttr("disabled"),e.preventDefault(),!1
            })
        })
    }
   
   function AeroDialogs(cont,title,fn,type){
	  var $id="dialog-"+getRnd()+"-"+type;//生成ID
	  f = {
		  id: $id,
		  icon: type,
		  WinTitle: '<span><b>'+title+'</b></span>',
		  type:type,
		  content: cont,
		  top:0,
		  left:0,
		  callback: typeof fn=='undefined'?$.noop:fn
	  };
	  if (type == "alert" || "success" || "error") f.buttons = AeroDialog.btn.OK;
	  switch (type) {
	  case "confirm":
		  f.buttons = AeroDialog.btn.OKCANCEL;
		  break;
	  case "warning":
		  f.buttons = AeroDialog.btn.YESNOCANCEL
	  }
	  var wbtn='<div class="winbtn-leftadge"></div><a id="'+f.id+"_"+AeroDialog.btn.CLOSE[0].result +'" href="javascript:void(0)" class="win-closebtn active" title="'+AeroDialog.btn.CLOSE[0].title+'"></a><div class="winbtn-rightedge"></div>';
	  
	  $(window.top.document).find('body').append(divCover());
	  $('body').append('<div id="'+$id+'" style="display: none;">'+MainAeroWindow(f.WinTitle,wbtn,DialogContent(f))+'</div>');
	  
	  $('.showContent').width($('.showContent').width()>AeroDialog.minWidth?AeroDialog.maxWidth:AeroDialog.minWidth);
	  var dtop=($(window).height())/2-200,dleft=($(window).width()/2)-($('.showContent').width()+60)/2;
	  $('#'+$id).css({top:'0px',left:dleft+'px'});
	  $('#'+$id).show();
	  $('#'+$id).animate({
	  	top:dtop+'px'
	  },300);
	  
	  $('#'+$id).css({width:$('#'+$id).width()+'px',height:$('#'+$id).height()+'px',position:'absolute'});

	  $('#'+$id).draggable({
		cursor: "move",
		cancel:'.tb-mm-dialog',
		drag:function(){}
			
	  });
	  //{queue:true,duration:200,easing:""}
	  callBack(f);
   }

   
   	function AddDialogBtn(bo) {//添加button按钮
	  var cx = [];
	  return $.each(bo.buttons, function ($, d) {
		  cx.push('<a class="dialogBtns" id="', bo.id, "_", d.result, '" href="javascript:void(0)"><span> ', d.value, " </span></a>")
	  }), cx.join("")
    }
   
   function DialogContent(aWin){
	 return ['<div class="tb-mm-dialog">',
	  '<table border="0" cellspacing="0" cellpadding="0">',
	  '  <tr>',
	  '	<td align="center"><img src="images/icons/',aWin.type,'.png" border="0"></td>',
	  '	<td><div class="showContent" style="margin:5px;"><p>',aWin.content,'</p></div></td>',
	  '	</tr>',
	  '	<tr>',
	  '	  <td colspan="2">',AddDialogBtn(aWin),
	  '	  </td>',
	  '	</tr>',
	  '</table>',
	  '</div>'].join('');
   }
  
  //用于回调事件处理
    AeroDialog.btn = {
	  OK: [{
		  value: AeroDialog.Btntxt.OK,
		  result: "ok"
	  }],
	  NO: [{
		  value: AeroDialog.Btntxt.NO,
		  result: "no"
	  }],
	  YES: [{
		  value: AeroDialog.Btntxt.YES,
		  result: "yes"
	  }],
	  CANCEL: [{
		  value: AeroDialog.Btntxt.CANCEL,
		  result: "cancel"
	  }],
	  CLOSE: [{
		  title: AeroDialog.Btntxt.CLOSE,
		  result: "close"
	  }]
	},
	AeroDialog.btn.OKCANCEL = AeroDialog.btn.CANCEL.concat(AeroDialog.btn.OK),
	AeroDialog.btn.YESNO = AeroDialog.btn.NO.concat(AeroDialog.btn.YES),
	AeroDialog.btn.YESNOCANCEL = AeroDialog.btn.CANCEL.concat(AeroDialog.btn.NO).concat(AeroDialog.btn.YES),
	
	AeroDialog.close=function(winID){
		//alert(divID);
		$('#'+winID).remove();
		$(window.top.document).find('#winDialogCover').remove();
	}
	
	AeroDialog.alert = function (cont,title,fn) {
	  AeroDialogs(cont,typeof title=="undefined"?"提示":title,fn,'alert');
	},
	AeroDialog.html = function (cont,title) {
		AeroDialogs(cont,title);
	}
    AeroDialog.confirm = function (cont,title,fn) {
		AeroDialogs(cont,title,fn,"confirm");
	},
	AeroDialog.prompt = function (cont,title,fn) {
	}, 
	AeroDialog.success = function (cont,title,fn) {
	   AeroDialogs(cont,title,fn, "success");
	}, 
	AeroDialog.warning = function (cont,title,fn) {
		AeroDialogs(cont,title,fn,"warning");
	}, 
	AeroDialog.error = function (cont,title,fn) {
		AeroDialogs(cont,title,fn, "error");
	},
	AeroDialog.error = function (cont,title,fn) {
		AeroDialogs(cont,title,fn, "question");
	}
})(jQuery);


$(function(){
	//添加任务栏
	if($('#AeroTaskbar').length==0&&AeroWindow.ShowTaskbar){
		var output = '<div id="AeroTaskbar" style="display:none" class="tskbg-hori horiBottom"><div id="StartMenu-Btn"></div><div id="TaskbarSeparate"></div> <div title="Show Desktop" id="TaskbarShowDesktop"></div><div id="computeInfo"></div>';
		output+='</div><div id="TaskbarSeparateRight"></div> </div>';
		$('body').append(output);
	  //$('body').append('<div id="Start-Menu"> </div>');
	}
	if(AeroWindow.ShowTaskbar){$('#AeroTaskbar').css('display','block');}
	if($('#DesktopIcons').length==0&&AeroWindow.ShowDesktop)
		$('body').append('<div id="DesktopIcons"></div>');
	$('body').append('<div class="AeroWindows"></div>');
	var stmenu=$('#Start-Menu')
	if(AeroWindow.ShowTaskbar)
	{
		var list="";
		if(stmenu.length==0)
			$('body').append('<div id="Start-Menu" class="Start-position"></div>');
		else
		{
			list=stmenu.html();
		}
		stmenu.load('ajaxload/StartMenu.html',function(){$('#NavItemsCenter').html(list);});
		
	}
	$('#StartMenu-Btn').live("mouseover mouseout",function(event){
		if(event.type=='mouseover')
			$(this).addClass('hover');
		else
			$(this).removeClass('hover');});
	$('#StartMenu-Btn').live("click",function(){
		if($(this).hasClass('active')){
			$(this).removeClass('active');
			//stmenu.css('display','block');
			stmenu.hide(200);}
		else{
			$(this).addClass('active');
			stmenu.show(200);}});

	
	function getOpenWindowsCount(){
		i=0;
		jQuery.each($('body').data('AeroWindows'),function(){
			if(this.get('WinStatus')!='minimized'&&this.get('WinStatus')!='closed'&&this.get('WinStatus')!='spreaded'){i+=1;}
			});
		return(i);
	};
	function minall(){
		jQuery.each($('body').data('AeroWindows'),function(){
			if(this.get('WinStatus')!='minimized'&&this.get('WinStatus')!='closed'&&this.get('WinStatus')!='spreaded'){
				this.ResizeWindow('minimize',false);}
		});
	};
	function resall(){
		jQuery.each($('body').data('AeroWindows'),function(){
			if(this.get('WinStatus')!='window'&&this.get('WinStatus')!='closed'){
				this.ResizeWindow('restore',false);}
	});};
	
	function transparentallon(){
	  jQuery.each($('body').data('AeroWindows'),function(){
		  if(this.get('WinStatus')!='minimized'&&this.get('WinStatus')!='closed'){
			  this.ResizeWindow('transparent-on',false);}
	  });
	};
   function transparentalloff(){
	  jQuery.each($('body').data('AeroWindows'),function(){
		  if(this.get('WinStatus')!='minimized'&&this.get('WinStatus')!='closed'){
			  this.ResizeWindow('transparent-off',false);}
	});};
	$('#TaskbarShowDesktop').live("mouseover mouseout",function(event){
		if(event.type=='mouseover'){
			$(this).addClass('hover');transparentallon();}
		else{
			$(this).removeClass('hover');
			transparentalloff();}
	});
	$('#TaskbarShowDesktop').live("click",function(){
		transparentalloff();
		if(getOpenWindowsCount()>0){minall();}
		else{resall();}
	});
	
	//当鼠标点击桌面或除菜单其他外的时候开始菜单关闭	
	$('html').click(function(event){
		var outClicked_startmenu=true;
		var outClicked_desktopicon=true;
		var outClicked_aerowindow=true;
		if((event.target.id=='Start-Menu')||($(event.target).parents('#StartMenu-Btn').length||event.target.id=='StartMenu-Btn')||($(event.target).parents('#SearchBox').length||event.target.id=='SearchBox')){outClicked_startmenu=false;}
		if($(event.target).parents('#DesktopIcons').length){outClicked_desktopicon=false;}
		if($(event.target).parents('.AeroWinContainer').length||$(event.target).hasClass('AeroWinContainer')||$(event.target).parents('.Taskbar-Item').length||$(event.target).hasClass('Taskbar-Item')){outClicked_aerowindow=false;}
		if(outClicked_startmenu){
			//$('#Start-Menu').css({visibility:'hidden'});
			stmenu.hide(200);
			$('#StartMenu-Btn').removeClass('active');}
		if(outClicked_desktopicon){
			$('#DesktopIcons div').removeClass('mouseclicked');
			$('#DesktopIcons div').removeClass('mouseout');}
		if(outClicked_aerowindow){
			$(".AeroWindow").removeClass('active');}
	});
	
});