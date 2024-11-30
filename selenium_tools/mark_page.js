// ADAPTED FROM https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/web-navigation/web_voyager.ipynb
// - change to window.[var] for Selenium
// - return elements
// - fix repeated declaration with var

// Set scrollbar CSS
if (!window.customCSS) {
  window.customCSS = `
    ::-webkit-scrollbar {
        width: 10px;
    }
    ::-webkit-scrollbar-track {
        background: #27272a;
    }
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 0.375rem;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
`;

  // Create new style tag to annotate elements on the page
  window.styleTag = document.createElement("style");
  styleTag.textContent = customCSS;
  document.head.append(styleTag);
}

window.labels = window.labels ?? [];

window.unmarkPage = () => {
  // Unmark page logic, removes every label
  for (const label of window.labels) {
    document.body.removeChild(label);
  }
  window.labels = [];
};

window.markPage = () => {
  unmarkPage();

  var bodyRect = document.body.getBoundingClientRect();

  // 1. call slice to copy the list
  // 2. select every element on the page
  var items = Array.prototype.slice
    .call(document.querySelectorAll("*"))
    .map(function (element) {
      // width and height of the WINDOW(root element)
      var vw = Math.max(
        document.documentElement.clientWidth || 0,
        window.innerWidth || 0
      );
      var vh = Math.max(
        document.documentElement.clientHeight || 0,
        window.innerHeight || 0
      );

      // Get text content, with multiple whitespace > " "
      var textualContent = element.textContent.trim().replace(/\s{2,}/g, " ");
      var elementType = element.tagName.toLowerCase();

      // aria-label is a text label for elements for accessibility
      var ariaLabel = element.getAttribute("aria-label") || "";

      // DOMrect, indicates bounding boxes. most elements should have only 1
      // filterout boxes not containing the element, using elementFromPoint
      // return data in a different format, along with width and height, for remaining rects
      var rects = [...element.getClientRects()]
        .filter((bb) => {
          var center_x = bb.left + bb.width / 2;
          var center_y = bb.top + bb.height / 2;
          var elAtCenter = document.elementFromPoint(center_x, center_y);

          return elAtCenter === element || element.contains(elAtCenter);
        })
        .map((bb) => {
          const rect = {
            left: Math.max(0, bb.left),
            top: Math.max(0, bb.top),
            right: Math.min(vw, bb.right),
            bottom: Math.min(vh, bb.bottom),
          };
          return {
            ...rect,
            width: rect.right - rect.left,
            height: rect.bottom - rect.top,
          };
        });

      // total area of all the rectangles
      var area = rects.reduce((acc, rect) => acc + rect.width * rect.height, 0);

      // Return elements that should be included, area, rects, etc.
      // Filter down to only elements to include, and items with large enough area
      return {
        element: element,
        include:
          element.tagName === "INPUT" ||
          element.tagName === "TEXTAREA" ||
          element.tagName === "SELECT" ||
          element.tagName === "BUTTON" ||
          element.tagName === "A" ||
          element.onclick != null ||
          window.getComputedStyle(element).cursor == "pointer" ||
          element.tagName === "IFRAME" ||
          element.tagName === "VIDEO",
        area,
        rects,
        text: textualContent,
        type: elementType,
        ariaLabel: ariaLabel,
      };
    })
    .filter((item) => item.include && item.area >= 20);

  // Only keep inner clickable items
  // remove items that are nested in other items, take the innermost child
  items = items.filter(
    (x) => !items.some((y) => x.element.contains(y.element) && !(x == y))
  );

  // Function to generate random colors
  function getRandomColor() {
    var letters = "0123456789ABCDEF";
    var color = "#";
    for (var i = 0; i < 6; i++) {
      color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
  }

  // Lets create a floating border on top of these elements that will always be visible
  // For each item, in the rects, we make a div, style it to be fixed on the screen with a border, set zindex
  items.forEach(function (item, index) {
    item.rects.forEach((bbox) => {
      newElement = document.createElement("div");
      var borderColor = getRandomColor();
      newElement.style.outline = `2px dashed ${borderColor}`;
      newElement.style.position = "fixed";
      newElement.style.left = bbox.left + "px";
      newElement.style.top = bbox.top + "px";
      newElement.style.width = bbox.width + "px";
      newElement.style.height = bbox.height + "px";
      newElement.style.pointerEvents = "none";
      newElement.style.boxSizing = "border-box";
      newElement.style.zIndex = 2147483647; // move to foreground basically
      // newElement.style.background = `${borderColor}80`;

      // Add floating label at the corner
      var label = document.createElement("span");
      label.textContent = index;
      label.style.position = "absolute";
      // These we can tweak if we want
      label.style.top = "-19px";
      label.style.left = "0px";
      label.style.background = borderColor;
      label.style.fontSize = "18px";
      label.style.fontWeight = "bold";
      // label.style.background = "black";
      label.style.color = "white";
      label.style.padding = "2px 4px";
      label.style.fontSize = "12px";
      label.style.borderRadius = "2px";
      newElement.appendChild(label);

      document.body.appendChild(newElement);
      window.labels.push(newElement);
      // item.element.setAttribute("-ai-label", label.textContent);
    });
  });

  // flat is like map() followed by a flat() call(flatten by 1 level)
  const coordinates = items.flatMap((item) =>
    item.rects.map(({ left, top, width, height }) => ({
      // x: (left + left + width) / 2,
      // y: (top + top + height) / 2,
      type: item.type,
      text: item.text,
      element: item.element, // new
      ariaLabel: item.ariaLabel,
    }))
  );

  // (x, y) of the center point of the element, type/text/aria-label
  return coordinates;
};
