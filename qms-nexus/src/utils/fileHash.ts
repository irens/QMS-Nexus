/**
 * 文件哈希计算工具
 * 使用 Web Crypto API 计算文件 SHA-256 哈希
 * 支持大文件分块计算，避免内存溢出
 */

/**
 * 计算文件的 SHA-256 哈希值
 * @param file 要计算哈希的文件
 * @returns 返回十六进制格式的哈希字符串
 */
export async function calculateFileHash(file: File): Promise<string> {
  const chunkSize = 1024 * 1024; // 1MB 分块
  const chunks = Math.ceil(file.size / chunkSize);

  const cryptoObj = window.crypto || (window as any).msCrypto;
  const subtle = cryptoObj.subtle;

  // 使用增量哈希算法
  // 由于 Web Crypto API 不直接支持增量哈希，我们采用以下策略：
  // 1. 对每个分块计算哈希
  // 2. 将所有分块哈希组合后再计算最终哈希
  const chunkHashes: ArrayBuffer[] = [];

  for (let i = 0; i < chunks; i++) {
    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, file.size);
    const chunk = file.slice(start, end);
    const chunkBuffer = await chunk.arrayBuffer();

    // 计算每个分块的哈希
    const chunkHash = await subtle.digest('SHA-256', chunkBuffer);
    chunkHashes.push(chunkHash);
  }

  // 将所有分块哈希合并并计算最终哈希
  const combinedLength = chunkHashes.reduce((sum, hash) => sum + hash.byteLength, 0);
  const combinedBuffer = new Uint8Array(combinedLength);
  let offset = 0;
  for (const hash of chunkHashes) {
    combinedBuffer.set(new Uint8Array(hash), offset);
    offset += hash.byteLength;
  }

  const finalHash = await subtle.digest('SHA-256', combinedBuffer);

  // 转换为十六进制字符串
  const hashArray = Array.from(new Uint8Array(finalHash));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * 快速计算文件哈希（适用于小文件，< 10MB）
 * @param file 要计算哈希的文件
 * @returns 返回十六进制格式的哈希字符串
 */
export async function calculateFileHashFast(file: File): Promise<string> {
  // 如果文件小于 10MB，直接计算整个文件的哈希
  if (file.size <= 10 * 1024 * 1024) {
    const cryptoObj = window.crypto || (window as any).msCrypto;
    const buffer = await file.arrayBuffer();
    const hash = await cryptoObj.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hash));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  // 大文件使用分块计算
  return calculateFileHash(file);
}

/**
 * 计算文本内容的 SHA-256 哈希
 * @param content 文本内容
 * @returns 返回十六进制格式的哈希字符串
 */
export async function calculateTextHash(content: string): Promise<string> {
  const cryptoObj = window.crypto || (window as any).msCrypto;
  const encoder = new TextEncoder();
  const buffer = encoder.encode(content);
  const hash = await cryptoObj.subtle.digest('SHA-256', buffer);
  const hashArray = Array.from(new Uint8Array(hash));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * 计算文件的部分哈希（用于快速预览）
 * 取文件开头、中间和结尾的部分数据进行哈希
 * @param file 要计算哈希的文件
 * @returns 返回十六进制格式的哈希字符串
 */
export async function calculatePartialHash(file: File): Promise<string> {
  const sampleSize = 64 * 1024; // 64KB 采样
  const samples: Blob[] = [];

  // 取文件开头
  samples.push(file.slice(0, sampleSize));

  // 取文件中间
  if (file.size > sampleSize * 2) {
    const midStart = Math.floor((file.size - sampleSize) / 2);
    samples.push(file.slice(midStart, midStart + sampleSize));
  }

  // 取文件结尾
  if (file.size > sampleSize) {
    samples.push(file.slice(file.size - sampleSize));
  }

  const cryptoObj = window.crypto || (window as any).msCrypto;
  const sampleBuffers: ArrayBuffer[] = [];

  for (const sample of samples) {
    sampleBuffers.push(await sample.arrayBuffer());
  }

  // 合并所有采样数据
  const totalLength = sampleBuffers.reduce((sum, buf) => sum + buf.byteLength, 0);
  const combinedBuffer = new Uint8Array(totalLength);
  let offset = 0;
  for (const buf of sampleBuffers) {
    combinedBuffer.set(new Uint8Array(buf), offset);
    offset += buf.byteLength;
  }

  const hash = await cryptoObj.subtle.digest('SHA-256', combinedBuffer);
  const hashArray = Array.from(new Uint8Array(hash));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * 去重检测结果类型
 */
export type DuplicateType = 'exact_match' | 'name_match' | 'new_file';

/**
 * 现有文档信息
 */
export interface ExistingDocument {
  id: string;
  title: string;
  filename: string;
  currentVersion: {
    id: string;
    versionNumber: number;
    versionLabel: string;
    status: string;
  };
}

/**
 * 去重检测结果
 */
export interface DuplicateCheckResult {
  type: DuplicateType;
  message: string;
  existingDocument?: ExistingDocument;
  suggestions: string[];
}

/**
 * 检查浏览器是否支持所需的 Crypto API
 * @returns 如果支持返回 true，否则返回 false
 */
export function isCryptoSupported(): boolean {
  const cryptoObj = window.crypto || (window as any).msCrypto;
  return !!(cryptoObj && cryptoObj.subtle && typeof cryptoObj.subtle.digest === 'function');
}

/**
 * 生成文件指纹（用于显示）
 * 返回哈希值的前 8 位
 * @param hash 完整的哈希值
 * @returns 短指纹字符串
 */
export function getFileFingerprint(hash: string): string {
  return hash.substring(0, 8).toUpperCase();
}
