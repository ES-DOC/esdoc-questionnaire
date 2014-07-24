
function render_mindmap_to_flashobject(fo,mindmap_path) {

    fo.addParam("quality", "high");
    fo.addParam("bgcolor", "#a0a0f0");
    fo.addVariable("openUrl", "_blank");
    fo.addVariable("startCollapsedToLevel","3");
    fo.addVariable("maxNodeWidth","200");
    fo.addVariable("mainNodeShape","elipse");
    fo.addVariable("justMap","false");
    fo.addVariable("initLoadFile",mindmap_path);
    fo.addVariable("defaultToolTipWordWrap",200);
    fo.addVariable("offsetX","left");
    fo.addVariable("offsetY","top");
    fo.addVariable("buttonsPos","top");
    fo.addVariable("min_alpha_buttons",20);
    fo.addVariable("max_alpha_buttons",100);
    fo.addVariable("scaleTooltips","false");

    fo.write("flashcontent");

};