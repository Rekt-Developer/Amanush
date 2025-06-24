<template>
    <div class="pb-3 relative bg-[var(--background-gray-main)]">
        <div
            class="flex flex-col gap-3 rounded-[22px] transition-all relative bg-[var(--fill-input-chat)] py-3 max-h-[300px] shadow-[0px_12px_32px_0px_rgba(0,0,0,0.02)] border border-black/8 dark:border-[var(--border-main)]">
            <div class="overflow-y-auto pl-4 pr-2">
                <textarea
                    class="flex rounded-md border-input focus-visible:outline-none focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 overflow-hidden flex-1 bg-transparent p-0 pt-[1px] border-0 focus-visible:ring-0 focus-visible:ring-offset-0 w-full placeholder:text-[var(--text-disable)] text-[15px] shadow-none resize-none min-h-[40px]"
                    :rows="rows" :value="modelValue"
                    @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
                    @compositionstart="isComposing = true" @compositionend="isComposing = false"
                    @keydown.enter.exact="handleEnterKeydown" :placeholder="t('Give Manus a task to work on...')"
                    :style="{ height: '46px' }"></textarea>
            </div>
            <footer class="flex flex-row justify-between w-full px-3">
                <div class="flex gap-2 pr-2 items-center">
                 <!-- 附件上传按钮 -->
                <label class="cursor-pointer flex items-center" title="上传附件">
                   <input
                       type="file"
                       class="hidden"
                       accept="*"
                       @change="handleFileChange"
                       :disabled="uploading"/>
                 <svg
                      v-if="!uploading"
                      xmlns="http://www.w3.org/2000/svg"
                      class="h-5 w-5 text-gray-500 hover:text-blue-500"
                      fill="none"
                       viewBox="0 0 24 24"
                       stroke="currentColor">
                     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l7.07-7.07a4 4 0 00-5.657-5.657l-7.07 7.07a6 6 0 108.485 8.485l6.586-6.586" />
                </svg>
                <span v-else class="text-xs text-gray-400 ml-1">上传中...</span>
              </label>
    <!-- 已上传附件展示 -->
    <div v-if="attachment" class="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded">
        <span class="text-xs">{{ attachment.filename }}</span>
        <button @click="removeAttachment" class="text-red-400 hover:text-red-600 text-xs ml-1">移除</button>
    </div>
</div>
                <div class="flex gap-2">
                    <button
                        v-if="!isRunning || hasTextInput"
                        class="whitespace-nowrap text-sm font-medium focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 text-primary-foreground hover:bg-primary/90 p-0 w-8 h-8 rounded-full flex items-center justify-center transition-colors hover:opacity-90"
                        :class="!hasTextInput ? 'cursor-not-allowed bg-[var(--fill-tsp-white-dark)]' : 'cursor-pointer bg-[var(--Button-primary-black)]'"
                        @click="handleSubmit">
                        <SendIcon :disabled="!hasTextInput" />
                    </button>
                    <button
                        v-else
                        @click="handleStop"
                        class="inline-flex items-center justify-center whitespace-nowrap text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring bg-[var(--Button-primary-black)] text-[var(--text-onblack)] gap-[4px] hover:opacity-90 rounded-full p-0 w-8 h-8">
                        <div class="w-[10px] h-[10px] bg-[var(--icon-onblack)] rounded-[2px]">
                        </div>
                    </button>
                </div>
            </footer>
        </div>
    </div>
</template>

<script setup lang="ts">
import {showErrorToast, showSuccessToast} from '../utils/toast'
import { uploadAttachment } from '../api/attachment';
import { ref, watch } from 'vue';
import SendIcon from './icons/SendIcon.vue';
import { useI18n } from 'vue-i18n';

// 附件相关
const attachment = ref<any>(null);
const uploading = ref(false);

const handleFileChange = async (event: Event) => {
    const files = (event.target as HTMLInputElement).files;
    if (!files || files.length === 0) return;
    const file = files[0];
    uploading.value = true;
    try {
        const data = await uploadAttachment(file);
        console.log('上传接口返回：', data);
        if (data) {
            attachment.value = data;
            showSuccessToast('上传成功');
        } else {
            showErrorToast('上传失败');
        }
    } catch (e) {
        showErrorToast('上传失败');
    } finally {
        uploading.value = false;
    }
};

// 移除附件
const removeAttachment = () => {
    attachment.value = null;
};

const { t } = useI18n();
const hasTextInput = ref(false);
const isComposing = ref(false);

const props = defineProps<{
    modelValue: string;
    rows: number;
    isRunning: boolean;
}>();

const emit = defineEmits<{
    (e: 'update:modelValue', value: string): void;
    (e: 'submit'): void;
    (e: 'stop'): void;
}>();

const handleEnterKeydown = (event: KeyboardEvent) => {
    if (isComposing.value) {
        // If in input method composition state, do nothing and allow default behavior
        return;
    }

    // Not in input method composition state and has text input, prevent default behavior and submit
    if (hasTextInput.value) {
        event.preventDefault();
        handleSubmit();
    }
};

const handleSubmit = () => {
    if (!hasTextInput.value) return;
    console.log('发送消息时的附件：', attachment.value);
    emit('submit', {
        message: props.modelValue,
        attachments: attachment.value ? [attachment.value] : [],
    });
    attachment.value = null;
};

const handleStop = () => {
    emit('stop');
};

watch(() => props.modelValue, (value) => {
    hasTextInput.value = value.trim() !== '';
});
</script>