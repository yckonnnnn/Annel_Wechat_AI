#include "WeWorkFinanceSdk_C.h"
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 用法: echo -n "<raw_aes_key>" | ./decrypt_helper "<encrypt_chat_msg>"
// AES 密钥通过 stdin 传入（二进制，避免 null byte 问题）
// 输出: 解密后的明文 JSON

int main(int argc, char* argv[]) {
    if (argc < 2) {
        fprintf(stderr, "usage: echo -n AES_KEY | %s encrypt_chat_msg\n", argv[0]);
        return 1;
    }

    // 从 stdin 读取 AES 密钥（最多 256 bytes）
    unsigned char aes_key[256];
    int key_len = fread(aes_key, 1, sizeof(aes_key), stdin);
    if (key_len <= 0) {
        fprintf(stderr, "读取 AES 密钥失败\n");
        return 1;
    }

    void* handle = dlopen("./libWeWorkFinanceSdk_C.so", RTLD_LAZY);
    if (!handle) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 1; }

    Slice_t* (*newslice)()         = dlsym(handle, "NewSlice");
    void    (*freeslice)(Slice_t*) = dlsym(handle, "FreeSlice");
    int (*decryptdata)(const char*, const char*, Slice_t*) = dlsym(handle, "DecryptData");

    Slice_t* msg_slice = newslice();
    int ret = decryptdata((const char*)aes_key, argv[1], msg_slice);

    if (ret == 0 && msg_slice->buf) {
        printf("%s", msg_slice->buf);
        fflush(stdout);
    } else {
        fprintf(stderr, "DecryptData err: %d\n", ret);
        freeslice(msg_slice);
        return 1;
    }

    freeslice(msg_slice);
    return 0;
}
