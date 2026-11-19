export const EXPORT_WATERMARK_TEXT = "yanling.fun";

/**
 * 在 canvas 上绘制斜向平铺水印（原地绘制，不修改 DOM）
 * @param {HTMLCanvasElement} canvas
 * @param {string} text
 */
export function drawTiledWatermark(canvas, text = EXPORT_WATERMARK_TEXT) {
  const ctx = canvas.getContext("2d");
  if (!ctx || canvas.width < 32 || canvas.height < 32) return;

  const { width, height } = canvas;
  const rotation = (-30 * Math.PI) / 180;
  const fontSize = Math.max(
    18,
    Math.min(36, Math.round(Math.min(width, height) * 0.026)),
  );
  const stepX = Math.max(220, fontSize * 9);
  const stepY = Math.max(150, fontSize * 6);

  ctx.save();
  ctx.font = `600 ${fontSize}px system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`;
  ctx.fillStyle = "rgba(80, 80, 80, 0.10)";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  let row = 0;
  for (let y = -stepY; y < height + stepY; y += stepY) {
    const offsetX = (row % 2) * (stepX * 0.5);
    for (let x = -stepX + offsetX; x < width + stepX; x += stepX) {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(rotation);
      ctx.fillText(text, 0, 0);
      ctx.restore();
    }
    row += 1;
  }
  ctx.restore();
}

function cloneWatermarkedCanvas(sourceCanvas, text = EXPORT_WATERMARK_TEXT) {
  const watermarkedCanvas = document.createElement("canvas");
  watermarkedCanvas.width = sourceCanvas.width;
  watermarkedCanvas.height = sourceCanvas.height;

  const ctx = watermarkedCanvas.getContext("2d");
  if (!ctx) return sourceCanvas;

  ctx.drawImage(sourceCanvas, 0, 0);
  drawTiledWatermark(watermarkedCanvas, text);
  return watermarkedCanvas;
}

/**
 * 将Canvas导出为图片并下载
 * 兼容处理移动端大图导出问题
 * @param {HTMLCanvasElement} canvas - canvas元素
 * @param {string} filename - 文件名
 */
export const downloadCanvasAsImage = (canvas, filename) => {
  const watermarkedCanvas = cloneWatermarkedCanvas(canvas);

  try {
    // 优先尝试使用 toBlob，因为它处理大文件更有效率且不容易崩溃
    if (watermarkedCanvas.toBlob) {
      watermarkedCanvas.toBlob((blob) => {
        if (!blob) {
          console.error("Canvas转换Blob失败");
          fallbackToDataURL(watermarkedCanvas, filename);
          return;
        }

        // 尝试使用 navigator.share (主要针对移动端)
        // 注意：navigator.share 需要在 HTTPS 环境下，且必须由用户手势触发
        // 这里作为一种尝试，如果失败则回退到下载链接
        if (
          navigator.share &&
          navigator.canShare &&
          navigator.canShare({
            files: [new File([blob], filename, { type: blob.type })],
          })
        ) {
          const file = new File([blob], filename, { type: blob.type });
          navigator
            .share({
              files: [file],
              title: "分享图片",
              text: filename,
            })
            .catch((err) => {
              console.log("分享失败，尝试下载:", err);
              downloadBlob(blob, filename);
            });
        } else {
          downloadBlob(blob, filename);
        }
      }, "image/png");
    } else {
      fallbackToDataURL(watermarkedCanvas, filename);
    }
  } catch (e) {
    console.error("导出图片出错:", e);
    fallbackToDataURL(watermarkedCanvas, filename);
  }
};

const downloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;

  // 兼容某些移动端浏览器，添加到body
  document.body.appendChild(link);

  try {
    link.click();
  } catch (e) {
    console.error("Link click failed", e);
  }

  // 清理
  document.body.removeChild(link);
  setTimeout(() => URL.revokeObjectURL(url), 100);
};

const fallbackToDataURL = (canvas, filename) => {
  try {
    const imgUrl = canvas.toDataURL("image/png");
    const link = document.createElement("a");
    link.href = imgUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (e) {
    console.error("DataURL导出失败:", e);
    // eslint-disable-next-line no-alert -- Preserve the existing native notification or confirmation flow.
    alert("导出图片失败，图片可能过大");
  }
};
