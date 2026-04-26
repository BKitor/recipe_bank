/*
	* Global.js
	*
	* @package      sallysbaking
	* @author       Lindsay Humes
	* @since        1.0.0
	* @license      GPL-2.0+
*/


jQuery(function ($) {
    //Counter function
    $("ol").each(function () {
        var val = 1;
        if ($(this).attr("start")) {
            val = $(this).attr("start");
        }
        val = val - 1;
        val = 'lis ' + val;
        $(this).css('counter-increment', val);
    });
    // Mobile Menu
    $('.menu-toggle').click(function () {
        $('.search-toggle, .header-search, .search-close').removeClass('active');
        $('.menu-toggle, .drawer-nav').toggleClass('active');
    });
    $('.menu-item-has-children > a').click(function (e) {
        $(this).parent().toggleClass('expanded');
        e.preventDefault();
    });
    $('.menu-item-has-children > .sub-menu-toggle').click(function (e) {
        $(this).parent().toggleClass('expanded');
        e.preventDefault();
    });
    $('.menu-item-has-children > .submenu-expand').click(function (e) {
        $(this).toggleClass('expanded');
        e.preventDefault();
    });
    // Search toggle
    $('.search-toggle, .search-close').click(function () {
        $('.search-toggle, .header-search, .search-close').toggleClass('active');
        $('.site-header .search-field').focus();
    });
        // var otherDiv = document.getElementById('banner-present');
    // if (otherDiv) {
    //   // If present, add class to the target div
    //   document.getElementById('main-header').classList.add('taller');
    //   document.getElementById('h-spacer').classList.add('taller');
    //   document.getElementById('main-content').classList.add('scroll-watch');
    //   document.getElementById('mobile-tog').classList.add('banner-pres');
    // }
    //
    var bannerDiv = document.getElementById('top-banner');
    if (bannerDiv) {
        document.getElementById('site-header').classList.add('full-header');
    }
    if (!bannerDiv) {
        // If not present, remove classes from the target divs
        var mainHeader = document.getElementById('site-header');
        if (mainHeader) {
            mainHeader.classList.remove('full-header');
        }
    }
    $(window).scroll(function(){
        if ($(this).scrollTop() > 50) {
            $('.site-header.full-header').addClass('hidden-banner');
            $('.top-banner').addClass('hidden-banner');
        } else {
            $('.site-header.full-header').removeClass('hidden-banner');
            $('.top-banner').removeClass('hidden-banner');
        }
    });
});
