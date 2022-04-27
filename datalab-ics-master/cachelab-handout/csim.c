//Written by Rachel Teal, Heather Dalton, and Owen Elliott

#include "cachelab.h"
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <string.h>
#include <math.h>

/* Whats left?
    finish verbose by making print options tied to flag presecence

    -Rachel and Heather
*/

/* Simple types for an address and for the value of the LRU counter */
typedef unsigned long mem_addr_t;
typedef unsigned long lru_t;
/* One cache line */
typedef struct {
  char valid;					/* Non-zero means line is valid */
  mem_addr_t tag;				/* Tag bits from address */
  lru_t lastAccessed;   		/* Least-recently-used value */
} cache_line_t;

/* One cache set: an array of E cache lines */
typedef cache_line_t* cache_set_t;
/* One cache: an array of S cache sets */
typedef cache_set_t* cache_t;

/* Global vars */
int hits = 0;
int misses = 0;
int evicts = 0;
lru_t lru_counter;
int verbose = 0;

int check_cache(mem_addr_t mem_addr, cache_t cache, int b, int s, int E) {
    
    mem_addr_t a_tag = mem_addr >> (b + s);
    mem_addr_t a_set = (mem_addr >> b) & ~(0xffffffff << s);
    
    cache_line_t* cache_ref = NULL;
    cache_line_t* stale_line = &cache[a_set][0];

    for(int i=0; i<E; i++){
        lru_counter++;
        cache_ref = &cache[a_set][i];
        if (cache_ref->valid && cache_ref->tag == a_tag){
            // Hit found!
            hits++;
            if (verbose) printf("hit ");
            cache_ref->lastAccessed = lru_counter;
            return 1;
        } else{
            if(!cache_ref->valid || cache_ref->lastAccessed < stale_line->lastAccessed){
                stale_line = cache_ref;
            }
        }
    }
    misses++;
    if (verbose) printf("miss ");

    if(stale_line->valid){
        if (verbose) printf("eviction ");
        evicts++;
    } else{
        stale_line->valid = 1;
    }
    stale_line->tag = a_tag;
    stale_line->lastAccessed = lru_counter;

    return 0;
}


int main(int argc, char *argv[])
{
    //Parse command arguments
    int opt;
    int s, E, b, S;
    char *path;
    
    s=-1;
    E=-1;
    b=-1;
    S=-1;
    lru_counter = 0;

    if(argc < 9){
        printf("Missing arguments.\n");
        exit(1);
    }

    if(argc > 11){
        printf("Too many arguments.\n");
        exit(1);
    }

    while((opt = getopt(argc, argv, "hvs:E:b:t:")) != -1){
        switch(opt){
            case 'v':
                verbose = 1;
                break;
            case 's':
                s = atoi(optarg);
                break;
            case 'E':
                E = atoi(optarg);
                break;
            case 'b':
                b = atoi(optarg);
                break;
            case 't':
                path = optarg;
                break;
            default:
            case 'h':
                printf("Usage: ./csim [-hv] -s <num> -E <num> -b <num> -t <file>\n"
                    "Options:\n"
                    "-h         Print this help message.\n"
                    "-v         Optional verbose flag.\n"
                    "-s <num>   Number of set index bits.\n"
                    "-E <num>   Number of lines per set.\n"
                    "-b <num>   Number of block offset bits.\n"
                    "-t <file>  Trace file.\n"
                    "\n"
                    "Examples:\n"
                    "linux>  ./csim -s 4 -E 1 -b 4 -t traces/yi.trace\n"
                    "linux>  ./csim -v -s 8 -E 2 -b 4 -t traces/yi.trace\n"
                );
                exit(1);
        }
    }

    if(s < 0){
        printf("Invalid -s argument.\n");
        exit(1);
    }
    if(E < 1){
        printf("Invalid -E argument.\n");
        exit(1);
    }
    if(b < 0){
        printf("Invalid -b argument.\n");
        exit(1);
    }

	S = (int) pow(2, s);

    /* How to allocate cache lines for one set. Generalize! */
    cache_t cache = malloc(S * sizeof(cache_set_t));
    memset(cache, 0, sizeof(*cache));
    //malloc((s*E*sizeof(cache_line_t))+(sizeof(cache_set_t)*s))
    //malloc(s * sizeof(one_set))
    //malloc(s*E*sizeof(cache_set_t))

    for (int i = 0; i < S; i++) {
        cache_set_t this_set = malloc(E * sizeof(cache_line_t));
        memset(this_set, 0, sizeof(*this_set));

        //Default vals here
        for (int j = 0; j < E; j++) {
            this_set[j].valid = 0;
            //this_set[j].tag = j;
            this_set[j].lastAccessed = lru_counter;
        }

        cache[i] = this_set;
        //free(this_set);
    }

    

    /* How to read from the trace file. */
    char operation;				/* The operation (I, L, S, M) */
	mem_addr_t address;			/* The address (in hex) */
	int size;					/* The size of the operation */

        //Open trace file
    FILE *fptr;
    
    if((fptr=fopen(path, "r"))== NULL){
        printf("Failed to open file!\n");
        exit(1);
    }
    
    while (fscanf(fptr, " %c %lx,%x\n", &operation, &address, &size) != EOF) {
        if (verbose) printf("%c %lx,%x ", operation, address, size);

        switch (operation){
            case 'I':
                break;
            case 'M':
            case 'L':
                check_cache(address, cache, b, s, E);
                if (operation == 'L') break;
            case 'S':
                check_cache(address, cache, b, s, E);
                break;
            default:
                printf("Operation not recognized: %c\n", operation);
                exit(1);
        }
        if (verbose) printf("\n");
	}
    fclose(fptr);

    for(int i = 0; i<S; i++){
        free(cache[i]);
    }

    free(cache);

    //call printSummary with counters
    printSummary(hits, misses, evicts); // Hits, misses, evictions
    return 0;
}