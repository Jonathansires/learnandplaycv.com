/*================================================
*
* Template name : Mono
* Version       : 8.2.1
* Author        : FlaTheme
* Author URL    : http://themeforest.net/user/flatheme
*
* Table of Contents : 
* 1.  Preloaders
* 2.  Scroll Animations
* 3.  Background Image
* 4.  Header Menu
* 5.  Fullscreen Menu
* 6.  ScrollToTop
* 7.  Portfolio Masonry
* 8.  Portfolio Grid
* 9.  Slider
* 10. Blog Masonry
* 11. Masonry
* 12. Lightbox
* 13. Parallax
* 14. Countdown
* 15. Counter
* 16. Accordion
* 17. Animated Progress bar
* 18. Easy Pie Chart
* 19. Google Maps
* 20. Contact Form
* 21. Cursor
* 22. Page Scroll Progress
* 23. Swiper
*
===============================================*/
"use strict";

var body = document.body;
var $windowWidth = $(window).width();

/*===============================================
  1. Preloaders
===============================================*/
window.addEventListener("load", function() {
  document.body.classList.add("loaded");
});


var preloaderType = body.getAttribute("data-preloader");

if (preloaderType === "1") {
  var preloader1 = document.createElement("div");
  preloader1.className = "preloader preloader-1";
  preloader1.innerHTML = "<div><svg class='loader-circular' viewBox='25 25 50 50'><circle class='loader-path' cx='50' cy='50' r='20'></svg></div>";
  body.appendChild(preloader1);
}
else if (preloaderType === "2") {
  var preloader2 = document.createElement("div");
  preloader2.className = "preloader preloader-2";
  preloader2.innerHTML = "<div><span></span></div>";
  body.appendChild(preloader2);
}
else if (preloaderType === "3") {
  var preloader3 = document.createElement("div");
  preloader3.className = "preloader preloader-3";
  preloader3.innerHTML = "<div><span></span></div>";
  body.appendChild(preloader3);
}


/*===============================================
  2. Scroll Animations
===============================================*/
scrollCue.init();


/*===============================================
  3. Background Image
===============================================*/
var bgImages = document.querySelectorAll(".bg-image");

if (bgImages) {
  bgImages.forEach(function(bgImage) {
    var bgData = bgImage.getAttribute("data-bg-src");
    bgImage.style.backgroundImage = 'url("' + bgData + '")';
  });
}


/*===============================================
  4. Header Menu
===============================================*/
var header = document.querySelector(".header");
var headerMenu = document.querySelector(".header-menu");
var headerToggle = document.querySelector(".header-toggle");
var headerSticky = document.querySelector(".header.sticky-autohide");
var c, currentScrollTop = 0;

//
// Auto Hide //
//
if (headerSticky) {
  window.addEventListener("scroll", function() {
    var a = window.pageYOffset;
    currentScrollTop = a;

    if (c < currentScrollTop && a > 210) {
      if (!headerMenu.classList.contains("show")) {
        headerSticky.classList.add("hide");
      }
    } else if (c > currentScrollTop && !(a <= 210)) {
      headerSticky.classList.remove("hide");
    }

    c = currentScrollTop;
  });
}

if (document.querySelector(".header.sticky-autohide:not(.header-lg, .header-xl, .transparent-light, .transparent-dark)")) {
  var headerPlaceholder = document.createElement("div");
  headerPlaceholder.className = "header-placeholder";
  document.querySelector(".header.sticky-autohide").insertAdjacentElement("beforebegin", headerPlaceholder);
}
if (document.querySelector(".header-lg.sticky-autohide:not(.transparent-light, .transparent-dark)")) {
  var headerPlaceholderLG = document.createElement("div");
  headerPlaceholderLG.className = "header-placeholder-lg";
  document.querySelector(".header-lg.sticky-autohide").insertAdjacentElement("beforebegin", headerPlaceholderLG);
}
if (document.querySelector(".header-xl.sticky-autohide:not(.transparent-light, .transparent-dark)")) {
  var headerPlaceholderXL = document.createElement("div");
  headerPlaceholderXL.className = "header-placeholder-xl";
  document.querySelector(".header-xl.sticky-autohide").insertAdjacentElement("beforebegin", headerPlaceholderXL);
}

//
// Sticky //
//
if (document.querySelector(".header.sticky:not(.header-lg, .header-xl, .transparent-light, .transparent-dark)")) {
  var headerPlaceholder = document.createElement("div");
  headerPlaceholder.className = "header-placeholder";
  document.querySelector(".header.sticky").insertAdjacentElement("beforebegin", headerPlaceholder);
}
if (document.querySelector(".header-lg.sticky:not(.transparent-light, .transparent-dark)")) {
  var headerPlaceholderLG = document.createElement("div");
  headerPlaceholderLG.className = "header-placeholder-lg";
  document.querySelector(".header-lg.sticky").insertAdjacentElement("beforebegin", headerPlaceholderLG);
}
if (document.querySelector(".header-xl.sticky:not(.transparent-light, .transparent-dark)")) {
  var headerPlaceholderXL = document.createElement("div");
  headerPlaceholderXL.className = "header-placeholder-xl";
  document.querySelector(".header-xl.sticky").insertAdjacentElement("beforebegin", headerPlaceholderXL);
}

//
// Transparent //
//
if (document.querySelector(".transparent-light")) {
  window.addEventListener("scroll", function() {
    var headerFixed = document.querySelectorAll(".header.sticky-autohide, .header.sticky");
    if (window.pageYOffset > 10) {
      headerFixed.forEach(function(header) {
        header.classList.remove("transparent-light");
      });
    } else {
      headerFixed.forEach(function(header) {
        header.classList.add("transparent-light");
      });
    }
  });
}
if (document.querySelector(".transparent-dark")) {
  window.addEventListener("scroll", function() {
    var headerFixed = document.querySelectorAll(".header.sticky-autohide, .header.sticky");
    if (window.pageYOffset > 10) {
      headerFixed.forEach(function(header) {
        header.classList.remove("transparent-dark");
      });
    } else {
      headerFixed.forEach(function(header) {
        header.classList.add("transparent-dark");
      });
    }
  });
}

//
// Open/Close Header Menu //
//
if (headerToggle) {
  headerToggle.addEventListener("click", function() {
    if (headerMenu.classList.contains("show")) {
      headerMenu.classList.remove("show");
      headerToggle.classList.remove("toggle-close");
    } else {
      headerMenu.classList.add("show");
      headerToggle.classList.add("toggle-close");
    }
  });
}
if (headerMenu) {
  document.addEventListener("click", function(e) {
    if (!e.target.closest(".header-menu, .header-toggle")) {
      if (headerMenu.classList.contains("show")) {
        headerMenu.classList.remove("show");
        headerToggle.classList.remove("toggle-close");
      }
    }
  });
}


//
// Dropdown Menu //
//
if (document.querySelector(".nav-dropdown")) {
  var navDropdowns = document.querySelectorAll(".nav-dropdown");
  var navSubdropdowns = document.querySelectorAll(".nav-subdropdown");

  navDropdowns.forEach(function(navDropdown) {
    var parentNavItem = navDropdown.parentNode;
    var navLink = parentNavItem.querySelector(".nav-link");
    navLink.classList.add("d-toggle");
    parentNavItem.insertAdjacentHTML("beforeend", '<a class="nav-dropdown-toggle" href="#"></a>');
  });

  navSubdropdowns.forEach(function(navSubdropdown) {
    var parentNavDropdownItem = navSubdropdown.parentNode;
    var navDropdownLink = parentNavDropdownItem.querySelector(".nav-dropdown-link");
    navDropdownLink.classList.add("sd-toggle");
    parentNavDropdownItem.insertAdjacentHTML("beforeend", '<a class="nav-subdropdown-toggle" href="#"></a>');
  });

  var navDropdownToggles = document.querySelectorAll(".nav-dropdown-toggle");
  navDropdownToggles.forEach(function(navDropdownToggle) {
    var parentNavItem = navDropdownToggle.parentNode;
    var navDropdown = parentNavItem.querySelector(".nav-dropdown");

    navDropdownToggle.addEventListener("click", function(e) {
      if (navDropdownToggle.classList.contains("active")) {
        navDropdownToggle.classList.remove("active");
        navDropdown.classList.remove("show");
      } else {
        navDropdownToggle.classList.add("active");
        navDropdown.classList.add("show");
      }
      e.preventDefault();
    });
  });

  var navSubdropdownToggles = document.querySelectorAll(".nav-subdropdown-toggle");
  navSubdropdownToggles.forEach(function(navSubdropdownToggle) {
    var parentNavDropdownItem = navSubdropdownToggle.parentNode;
    var navSubdropdown = parentNavDropdownItem.querySelector(".nav-subdropdown");

    navSubdropdownToggle.addEventListener("click", function(e) {
      if (navSubdropdownToggle.classList.contains("active")) {
        navSubdropdownToggle.classList.remove("active");
        navSubdropdown.classList.remove("show");
      } else {
        navSubdropdownToggle.classList.add("active");
        navSubdropdown.classList.add("show");
      }
      e.preventDefault();
    });
  });

  //
  // Mega Dropdown //
  //
  var navMegaMenu = document.querySelectorAll(".mega-menu-content");
  navMegaMenu.forEach(function(navMega) {
    var parentMegaItem = navMega.parentNode;
    var navMegaLink = parentMegaItem.querySelector(".nav-link");
    navMegaLink.classList.add("d-toggle");
    parentMegaItem.insertAdjacentHTML("beforeend", '<a class="nav-dropdown-toggle" href="#"></a>');
  });

  var megaMenuToggles = document.querySelectorAll(".mega-menu-item .nav-dropdown-toggle");
  megaMenuToggles.forEach(function(megaMenuToggle) {
    var parentMegaMenuItem = megaMenuToggle.parentNode;
    var megaMenu = parentMegaMenuItem.querySelector(".mega-menu-content");

    megaMenuToggle.addEventListener("click", function(e) {
      if (megaMenuToggle.classList.contains("active")) {
        megaMenuToggle.classList.remove("active");
        megaMenu.classList.remove("show");
      } else {
        megaMenuToggle.classList.add("active");
        megaMenu.classList.add("show");
      }
      e.preventDefault();
    });
  });
}


/*===============================================
  5. Fullscreen Menu
===============================================*/
var fm = document.querySelector(".fullscreen-menu");

if (fm) {
  var fmToggle = document.querySelector(".fm-toggle");
  var fmClose = document.querySelector(".fm-close");

  // Open //
  fmToggle.addEventListener("click", function() {
    if (fm.classList.contains("fm-show")) {
      fm.classList.remove("fm-show");
    } else {
      fm.classList.add("fm-show");
    }
  });

  // Close //
  fmClose.addEventListener("click", function() {
    fm.classList.remove("fm-show");
    fmToggle.classList.remove("fm-toggle-hide");
  });
}


/*===============================================
  6. Scroll To Top
===============================================*/
var scrollTopBtn = document.querySelector(".scrolltotop");

if (scrollTopBtn) {
  // Show/Hide button //
  window.addEventListener("scroll", function() {
    if (window.pageYOffset > 700) { // 700px from top
      scrollTopBtn.classList.add("scrolltotop-show");
    } else {
      scrollTopBtn.classList.remove("scrolltotop-show");
    }
  });
}


/*===============================================
  7. Portfolio Masonry
===============================================*/
var pMasonry = document.querySelector(".portfolio-masonry");

if (pMasonry) {
  imagesLoaded(pMasonry, function() {
    var pWrapper = $(".portfolio-masonry").isotope({
      itemSelector: ".portfolio-item",
      transitionDuration: 250 // 0.25 second
    });
    var filter = $(".filter ul li");

    // Portfolio Filter //
    filter.on("click", function() {
      var filterValue = $(this).attr("data-filter");
      pWrapper.isotope({ filter: filterValue });

      filter.removeClass("active");
      $(this).addClass("active");
    });
  });
}


/*===============================================
  8. Portfolio Grid
===============================================*/
var pGrid = document.querySelector(".portfolio-grid");

if (pGrid) {
  var mixer = mixitup('.portfolio-grid', {
    selectors: {
      target: '.portfolio-item'
    },
    animation: {
      duration: 250
    }
  });
}


/*===============================================
  9. Slider
===============================================*/
var owlSlider = document.querySelector(".owl-carousel");

if (owlSlider) {
  $(".owl-carousel").each( function() {
    var $carousel = $(this);

    var $defaults = {
      rewind: true,
      navText: ["<i class='bi bi-arrow-left-short'></i>","<i class='bi bi-arrow-right-short'></i>"],
      autoHeight: true, 
      autoplayTimeout: 4000, 
      autoplaySpeed: 400, 
      autoplayHoverPause: true, 
      navSpeed: 300, 
      dotsSpeed: 300
    }

    var $options = {
      items: $carousel.data("owl-items"),
      margin: $carousel.data("owl-margin"),
      loop: $carousel.data("owl-loop"),
      center: $carousel.data("owl-center"),
      nav: $carousel.data("owl-nav"),
      rewind: $carousel.data("owl-rewind"),
      dots: $carousel.data("owl-dots"),
      autoplay: $carousel.data("owl-autoplay")
    }

    var $responsive = {
      responsive: {
        0 : {
          items: $carousel.data("owl-xs")
        },
        576 : {
          items: $carousel.data("owl-sm")
        },
        768 : {
          items: $carousel.data("owl-md")
        },
        992 : {
          items: $carousel.data("owl-lg")
        },
        1200 : {
          items: $carousel.data("owl-xl")
        }
      }
    }

    $carousel.owlCarousel( $.extend( $defaults, $options, $responsive) );
  });
}


/*===============================================
  10. Blog Masonry
===============================================*/
var blogMasonry = document.querySelector(".blog-masonry");

if (blogMasonry) {
  imagesLoaded(blogMasonry, function() {
    var $blogMasonry = $(blogMasonry);
    $blogMasonry.masonry({
      itemSelector: '.blog-post-box'
    });
  });
}


/*===============================================
  11. Masonry
===============================================*/
var masonryGrid = document.querySelector(".masonry");

if (masonryGrid) {
  imagesLoaded(masonryGrid, function() {
    var $masonryGrid = $(masonryGrid);
    $masonryGrid.masonry({
      itemSelector: '.masonry-item'
    });
  });
}



/*===============================================
  12. Lightbox
===============================================*/
//
// Lightbox - Image //
//
var $lightboxImage = $(".lightbox-image-link, .lightbox-image-box");

$lightboxImage.each(function () {
  var $this = $(this);
  $this.magnificPopup({
    type: 'image',
    fixedContentPos: false,
    removalDelay: 200,
    closeOnContentClick: true, 
    image: {
      titleSrc: 'data-image-title'
    }
  });
});

//
// Lightbox - Media //
//
var $lightboxMedia = $(".lightbox-media-link, .lightbox-media-box");

$lightboxMedia.each(function() {
  var $this = $(this);
  $this.magnificPopup({
    type: "iframe",
    fixedContentPos: false,
    removalDelay: 200,
    preloader: false,
    iframe: {
      patterns: {
        youtube: {
          index: 'youtube.com/',
          id: 'v=',
          src: '//www.youtube.com/embed/%id%?autoplay=1&rel=0'
        },
          vimeo: {
          index: 'vimeo.com/',
          id: '/',
          src: '//player.vimeo.com/video/%id%?autoplay=1'
        }
      },
      srcAction: "iframe_src" 
    }
  });
});

//
// Lightbox - Gallery //
//
var $gallery = $(".gallery-wrapper");

if ($gallery.length) {
  $gallery.each(function() {
    var $this = $(this);
    $this.magnificPopup({
      delegate: 'a',
      removalDelay: '200',
      type: 'image',
      fixedContentPos: false,
      gallery: {
          enabled: true
      },
      image: {
        titleSrc: 'data-gallery-title'
      }
    });
  });
}


/*===============================================
  13. Parallax
===============================================*/
if ($windowWidth > 1200) {
  var parallaxBg = $(".parallax");

  if (parallaxBg.length) {
    parallaxBg.each(function() {
      $(this).parallaxie({
        speed: 0.2
      });
    });
  }
}


/*===============================================
  14. Countdown
===============================================*/
$(".countdown").each(function() {
  var finalDate = $(this).attr('data-countdown');

  $(this).countdown(finalDate, function(event) {
    $(this).html(event.strftime('%D days %H:%M:%S'));
  });
});


/*===============================================
  15. Counter
===============================================*/
$(".counter").appear(function() {

  $(this).each(function () {
    $(this).prop("Counter",0).animate({
        Counter: $(this).text()
    }, {
        duration: 2500,
        easing: "swing",
        step: function (now) {
            $(this).text(Math.ceil(now));
        }
    });
  });
  
},{accX: 0, accY: -10});


/*===============================================
  16. Accordion
===============================================*/
var accordionTitles = document.querySelectorAll(".accordion-title");

accordionTitles.forEach(function (accordionTitle) {
  accordionTitle.addEventListener("click", function () {
    var accordionList = accordionTitle.parentElement;
    var accordionContent = accordionTitle.nextElementSibling;

    if (accordionList.classList.contains("active")) {
      accordionList.classList.remove("active");
      accordionContent.style.maxHeight = null;
    } else {
      accordionList.classList.add("active");
      if (accordionTitle.closest(".accordion").classList.contains("single-open")) {
        var accordionItems = accordionTitle.closest(".accordion").querySelectorAll("li");
        accordionItems.forEach(function (item) {
          item.classList.remove("active");
        });
        accordionList.classList.add("active");
        accordionTitle.closest(".single-open").querySelectorAll(".accordion-content").forEach(function (content) {
          content.style.maxHeight = "0";
        });
      }
      accordionContent.style.maxHeight = accordionContent.scrollHeight + "px";
    }
  });

  //
  // Give max-height to Accordion's active content //
  //
  var accordion = accordionTitle.parentElement.closest(".accordion");
  if (accordion.querySelector("li.active")) {
    var accordionActiveContent = accordion.querySelector("li.active .accordion-content");
    var accordionHeight = accordionActiveContent.scrollHeight;
    accordionActiveContent.style.maxHeight = accordionHeight + "px";
  }
});


/*===============================================
  17. Animated Progress bar
===============================================*/
$(".animated-progress div").each(function () {
  $(this).appear(function () {
    $(this).css("width", $(this).attr("data-progress") + "%");
  },{accX: 0, accY: -10})
});


/*===============================================
  18. Easy Pie Chart
===============================================*/
$(".pie-chart").appear(function() {

  $(this).each(function() {
    $(this).easyPieChart({
      lineCap: 'square',
      onStep: function(from, to, percent) {
        $(this.el).find('.percent').text(Math.round(percent));
      }
    });
  });
  
},{accX: 0, accY: -10});


/*===============================================
  19. Google Maps
===============================================*/
var mapCanvas = $(".gmap");

if (mapCanvas.length) {
  var m,divId,initLatitude, initLongitude, map;

  for (var i = 0; i < mapCanvas.length; i++) {
    m = mapCanvas[i];

    initLatitude = m.dataset["latitude"];
    initLongitude = m.dataset["longitude"];
    divId = "#"+ m["id"];

    map = new GMaps({
      el: divId,
      lat: initLatitude,
      lng: initLongitude,
      zoom: 16,
      scrollwheel: false,
      styles: [
          /* style your map at https://snazzymaps.com/editor and paste JSON here */
      ]
    });

    map.addMarker({
      lat : initLatitude,
      lng : initLongitude
    });
  }
}


/*===============================================
  20. Contact Form
===============================================*/
$("#contactform").on("submit", function(e) {
  var name = $("#name").val();
  var email = $("#email").val();
  var subject = $("#subject").val();
  var message = $("#message").val();

  if (name === "") {
    $("#name").addClass("error-color");
  }
  if (email === "") {
    $("#email").addClass("error-color");
  }
  if (subject === "") {
    $("#subject").addClass("error-color");
  }
  if (message === "") {
    $("#message").addClass("error-color");
  }

  else {
    $.ajax({
      url:"assets/php/contact-form.php",
      data:$(this).serialize(),
      type:"POST",
      success:function(data){
        $("#success").addClass("show-result"); //=== Show Success Message==
        $("#contactform").each(function(){
          this.reset();
        });
      },
      error:function(data){
        $("#error").addClass("show-result"); //===Show Error Message====
      }
    });
    var forms = $("#contactform input, #contactform textarea");
    forms.removeClass("error-color");
  }

  e.preventDefault();
});


/*===============================================
  21. Cursor
===============================================*/
var customCursor = document.getElementById("cursor");

if (customCursor) {
  var cursor = document.getElementById("cursor");
  document.addEventListener('mousemove', function(e) {
    cursor.style.left = e.pageX + 'px';
    cursor.style.top = e.pageY + 'px';
  });

  var mouseElms = document.querySelectorAll("a, button, input, textarea, .accordion-title, .filter li");

  mouseElms.forEach(function(mouseElm) {
    mouseElm.addEventListener("mouseenter", function() {
      cursor.classList.add("scale-cursor");
    });
    mouseElm.addEventListener("mouseleave", function() {
      cursor.classList.remove("scale-cursor");
    });
  });
}


/*===============================================
  22. Page Scroll Progress
===============================================*/
var pageProgress = $(".page-progress-container");
if (pageProgress.length) {
  window.onscroll = function() {pageScrollFunction()};
  function pageScrollFunction() {
    var winScroll = document.body.scrollTop || document.documentElement.scrollTop;
    var height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    var scrolled = (winScroll / height) * 100;
    document.getElementById("pageProgress").style.width = scrolled + "%";
  }
}


/*===============================================
  23. Swiper
===============================================*/
var swiper = new Swiper(".hero-portfolio-slider", {
  slidesPerView: 1,
  spaceBetween: 30,
  // Responsive breakpoints
  breakpoints: {
    // when window width is >= 768px
    768: {
      slidesPerView: 2,
      spaceBetween: 30
    },
    // when window width is >= 992px
    992: {
      slidesPerView: 2,
      spaceBetween: 40
    },
    // when window width is >= 1200px
    1200: {
      slidesPerView: 2,
      spaceBetween: 50
    }
  },
  centeredSlides: true,
  grabCursor: true,
  pagination: {
    el: ".swiper-pagination",
    clickable: true,
  },
});