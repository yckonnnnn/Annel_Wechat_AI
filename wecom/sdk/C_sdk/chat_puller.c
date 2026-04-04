#include "WeWorkFinanceSdk_C.h"
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// 用法: ./chat_puller <corpid> <secret> <seq> <limit>
// 输出: GetChatData 返回的原始 JSON（加密消息）

int main(int argc, char* argv[]) {
    if (argc < 5) {
        fprintf(stderr, "usage: %s corpid secret seq limit\n", argv[0]);
        return 1;
    }

    void* handle = dlopen("./libWeWorkFinanceSdk_C.so", RTLD_LAZY);
    if (!handle) {
        fprintf(stderr, "dlopen failed: %s\n", dlerror());
        return 1;
    }

    WeWorkFinanceSdk_t* (*newsdk)()          = dlsym(handle, "NewSdk");
    int (*init)(WeWorkFinanceSdk_t*, const char*, const char*) = dlsym(handle, "Init");
    int (*getchatdata)(WeWorkFinanceSdk_t*, unsigned long long, unsigned int, const char*, const char*, int, Slice_t*) = dlsym(handle, "GetChatData");
    Slice_t* (*newslice)()                   = dlsym(handle, "NewSlice");
    void (*freeslice)(Slice_t*)              = dlsym(handle, "FreeSlice");
    int (*decryptdata)(const char*, const char*, Slice_t*) = dlsym(handle, "DecryptData");

    WeWorkFinanceSdk_t* sdk = newsdk();
    int ret = init(sdk, argv[1], argv[2]);
    if (ret != 0) {
        fprintf(stderr, "Init failed: %d\n", ret);
        return 1;
    }

    unsigned long long seq   = (unsigned long long)atoll(argv[3]);
    unsigned int       limit = (unsigned int)atoi(argv[4]);

    Slice_t* chat_slice = newslice();
    ret = getchatdata(sdk, seq, limit, "", "", 5, chat_slice);
    if (ret != 0) {
        fprintf(stderr, "GetChatData failed: %d, data: %s\n", ret, chat_slice->buf ? chat_slice->buf : "null");
        freeslice(chat_slice);
        return 1;
    }

    if (chat_slice->buf) {
        printf("%s", chat_slice->buf);
        fflush(stdout);
    }

    freeslice(chat_slice);
    return 0;
}
