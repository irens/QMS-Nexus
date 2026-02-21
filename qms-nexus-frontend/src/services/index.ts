// 服务统一导出
export { apiClient, ApiRequestError } from './api'
export { chatService, type AskRequest, type AskResponse, type ChatMessage } from './chat'
export { documentService, tagService, type DocumentQuery } from './document'
export { uploadService, type UploadOptions } from './upload'
export { systemService, type SystemStats, type SystemConfig } from './system'
export { correctionService, type Correction, type CorrectionCreate, type CorrectionUpdate } from './correction'
export { authService, type ApiKey, type IpWhitelist, type AuthConfig } from './auth'
export { 
  knowledgeBaseService, 
  type KnowledgeBase, 
  type KnowledgeBaseCreate,
  type KnowledgeBaseUpdate 
} from './knowledgeBase'

// 默认导出所有服务
import { apiClient } from './api'
import { chatService } from './chat'
import { documentService, tagService } from './document'
import { uploadService } from './upload'
import { systemService } from './system'
import { correctionService } from './correction'
import { authService } from './auth'
import { knowledgeBaseService } from './knowledgeBase'

export default {
  api: apiClient,
  chat: chatService,
  documents: documentService,
  tags: tagService,
  upload: uploadService,
  system: systemService,
  correction: correctionService,
  auth: authService,
  knowledgeBase: knowledgeBaseService
}
