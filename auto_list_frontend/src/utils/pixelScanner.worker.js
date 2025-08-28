// 使用 'self' 替代 'window' 在 worker 环境中
self.addEventListener('message', ({ data }) => {
  const { imageData, targetColor, tolerance } = data;
  const { width, height } = imageData;
  const pixelData = imageData.data;
  const positions = [];
  
  // 像素颜色对比函数（带容差）
  const isColorMatch = (r, g, b, a) => {
    return (
      Math.abs(r - targetColor.r) <= tolerance &&
      Math.abs(g - targetColor.g) <= tolerance &&
      Math.abs(b - targetColor.b) <= tolerance &&
      Math.abs(a - (targetColor.a ?? 255)) <= (tolerance * 2) // alpha 容差加倍
    );
  };
  
  // 遍历所有像素
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4;
      const r = pixelData[idx];
      const g = pixelData[idx + 1];
      const b = pixelData[idx + 2];
      const a = pixelData[idx + 3];
      
      if (isColorMatch(r, g, b, a)) {
        positions.push({ x, y });
      }
    }
  }
  
  self.postMessage(positions);
});