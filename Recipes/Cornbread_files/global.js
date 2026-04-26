/*
	* Global.js
	*
	* @package      sallysbakingrecipes
	* @author       Lindsay Humes
	* @since        1.0.0
	* @license      GPL-2.0+
*/
jQuery(function($){$('.menu-toggle').click(function(){$('.search-toggle, .header-search, .search-close').removeClass('active');$('.menu-toggle, .drawer-nav').toggleClass('active')});$('.menu-item-has-children > a').click(function(e){$(this).parent().toggleClass('expanded');e.preventDefault()});$('.menu-item-has-children > .sub-menu-toggle').click(function(e){$(this).parent().toggleClass('expanded');e.preventDefault()});$('.menu-item-has-children > .submenu-expand').click(function(e){$(this).toggleClass('expanded');e.preventDefault()});$('.search-toggle, .search-close').click(function(){$('.search-toggle, .header-search, .search-close').toggleClass('active');$('.site-header .search-field').focus()})})