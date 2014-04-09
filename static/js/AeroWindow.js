// JavaScript Document
//Date:2012-3-15
//Author:Andy
(function($){
	var AeroWindowPlugin=function(element,options){//插件定义
		var settings=$.extend({
			WinTitle:'AeroWindow for jQuery',//标题
			WinDraggable:true,//拖动窗体
			WinStatus:'window',//窗体状态
			WinType:'window',//alert,question,confirm,error,info
			WinResizable:true,//是否可以改变窗口大小
			WinAnimation : {
				Speed:500,//效果延迟时间，单位是毫秒
				AnimationMode:'easeOutCubic',//特效方式
				TransparentSpeed:300,//透明效果时间
			},
			WinIconFile:'images/icons/default.png',//默认窗口左上角图标
			WinPositionTop:200,//{center/值}初始时离桌面最上边位置
			WinPositionLeft:100,//{center/值}初始时离桌面最左边位置
			WinSize : {
				OuterWidth:300,//{atuo/值}内宽
				OuterHeight:300,//{atuo/值}内高
				MinWidth:100,//最小时的宽度
				MinHeight:100,//最小时允许的高度
				BorderWidth:22,
				BorderHeight:62,
			},
			WinButton : {
				Maximize:true,//显示最大化按钮
				Minimize:true,//显示最小化按钮
				Closable:true,//显示关闭按钮
			},
			LoadiFrameContentLater:false,//是否允许加载iframe链接内容
			WinElementID:this.id,//指定窗体ID
			WinBorderMouseCursorSpacing:25,//鼠标指针宽度
			WinDesktopIcon:true,//在桌面显示图标，在显示任何窗体的时候
			Taskbar:{
				Height:40,//状态栏高度
				display:true,
				position:'bottom',//left,right,top
			}
		},options||{});//可扩展
	}
	

});