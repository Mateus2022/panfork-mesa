/*
 * Copyright © 2022 Collabora, LTD
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice (including the next
 * paragraph) shall be included in all copies or substantial portions of the
 * Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */

#include "vk_pipeline.h"

#include "vk_log.h"
#include "vk_nir.h"
#include "vk_shader_module.h"
#include "vk_util.h"

#include "nir_serialize.h"

#include "util/mesa-sha1.h"

VkResult
vk_pipeline_shader_stage_to_nir(struct vk_device *device,
                                const VkPipelineShaderStageCreateInfo *info,
                                const struct spirv_to_nir_options *spirv_options,
                                const struct nir_shader_compiler_options *nir_options,
                                void *mem_ctx, nir_shader **nir_out)
{
   VK_FROM_HANDLE(vk_shader_module, module, info->module);
   const gl_shader_stage stage = vk_to_mesa_shader_stage(info->stage);

   assert(info->sType == VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO);

   if (module != NULL && module->nir != NULL) {
      assert(module->nir->info.stage == stage);
      assert(exec_list_length(&module->nir->functions) == 1);
      ASSERTED const char *nir_name =
         nir_shader_get_entrypoint(module->nir)->function->name;
      assert(strcmp(nir_name, info->pName) == 0);

      nir_validate_shader(module->nir, "internal shader");

      nir_shader *clone = nir_shader_clone(mem_ctx, module->nir);
      if (clone == NULL)
         return vk_error(device, VK_ERROR_OUT_OF_HOST_MEMORY);

      assert(clone->options == NULL || clone->options == nir_options);
      clone->options = nir_options;

      *nir_out = clone;
      return VK_SUCCESS;
   }

   const uint32_t *spirv_data;
   uint32_t spirv_size;
   if (module != NULL) {
      spirv_data = (uint32_t *)module->data;
      spirv_size = module->size;
   } else {
      const VkShaderModuleCreateInfo *minfo =
         vk_find_struct_const(info->pNext, SHADER_MODULE_CREATE_INFO);
      if (unlikely(minfo == NULL)) {
         return vk_errorf(device, VK_ERROR_UNKNOWN,
                          "No shader module provided");
      }
      spirv_data = minfo->pCode;
      spirv_size = minfo->codeSize;
   }

   nir_shader *nir = vk_spirv_to_nir(device, spirv_data, spirv_size, stage,
                                     info->pName, info->pSpecializationInfo,
                                     spirv_options, nir_options, mem_ctx);
   if (nir == NULL)
      return vk_errorf(device, VK_ERROR_UNKNOWN, "spirv_to_nir failed");

   *nir_out = nir;

   return VK_SUCCESS;
}

void
vk_pipeline_hash_shader_stage(const VkPipelineShaderStageCreateInfo *info,
                              unsigned char *stage_sha1)
{
   VK_FROM_HANDLE(vk_shader_module, module, info->module);

   if (module && module->nir) {
      /* Internal NIR module: serialize and hash the NIR shader.
       * We don't need to hash other info fields since they should match the
       * NIR data.
       */
      assert(module->nir->info.stage == vk_to_mesa_shader_stage(info->stage));
      ASSERTED nir_function_impl *entrypoint = nir_shader_get_entrypoint(module->nir);
      assert(strcmp(entrypoint->function->name, info->pName) == 0);
      assert(info->pSpecializationInfo == NULL);

      struct blob blob;

      blob_init(&blob);
      nir_serialize(&blob, module->nir, false);
      assert(!blob.out_of_memory);
      _mesa_sha1_compute(blob.data, blob.size, stage_sha1);
      blob_finish(&blob);
      return;
   }

   struct mesa_sha1 ctx;

   _mesa_sha1_init(&ctx);
   if (module) {
      _mesa_sha1_update(&ctx, module->sha1, sizeof(module->sha1));
   } else {
      const VkShaderModuleCreateInfo *minfo =
         vk_find_struct_const(info->pNext, SHADER_MODULE_CREATE_INFO);
      unsigned char spirv_sha1[SHA1_DIGEST_LENGTH];

      assert(minfo);
      _mesa_sha1_compute(minfo->pCode, minfo->codeSize, spirv_sha1);
      _mesa_sha1_update(&ctx, spirv_sha1, sizeof(spirv_sha1));
   }

   _mesa_sha1_update(&ctx, info->pName, strlen(info->pName));

   assert(util_bitcount(info->stage) == 1);
   _mesa_sha1_update(&ctx, &info->stage, sizeof(info->stage));

   if (info->pSpecializationInfo) {
      _mesa_sha1_update(&ctx, info->pSpecializationInfo->pMapEntries,
                        info->pSpecializationInfo->mapEntryCount *
                        sizeof(*info->pSpecializationInfo->pMapEntries));
      _mesa_sha1_update(&ctx, info->pSpecializationInfo->pData,
                        info->pSpecializationInfo->dataSize);
   }
   _mesa_sha1_final(&ctx, stage_sha1);
}
