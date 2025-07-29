import math

# Define constants for memory simulation
L1_CACHE_SIZE = 1024  # 1KB
L2_CACHE_SIZE = 16 * 1024 # 16KB

class Block:
    """Represents a single block in a cache."""
    def __init__(self):
        self.valid = False
        self.writeback = False
        self.tag = 0
        self.last_used_time = 0

class Cache:
    """Represents a cache in the memory hierarchy."""
    def __init__(self, size, block_size, associativity, wb=True):
        if block_size == 0 or associativity == 0:
            raise ValueError("Block size and associativity must be non-zero.")
        self.size = size
        self.block_size = block_size
        self.associativity = associativity
        self.num_blocks = size // block_size
        if self.num_blocks % associativity != 0:
            raise ValueError("Size, block_size, and associativity result in non-integer number of sets.")
        self.num_sets = self.num_blocks // associativity
        self.blocks = [[Block() for _ in range(associativity)] for _ in range(self.num_sets)]
        self.wb = wb

        # Statistics
        self.total_accesses = 0
        self.hits = 0
        self.misses = 0
        self.writebacks = 0
        
        # LRU timestamp
        self.time = 0

    def access(self, address, writeBack=False):
        """
        Accesses the cache with a given memory address.
        Returns True for a hit, False for a miss.
        """
        self.total_accesses += 1
        self.time += 1
        
        index = (address // self.block_size) % self.num_sets
        tag = address // (self.block_size * self.num_sets)
        set_blocks = self.blocks[index]

        # Search for a hit
        for block in set_blocks:
            if block.valid and block.tag == tag:
                self.hits += 1
                block.last_used_time = self.time
                if writeBack:
                    block.writeback = True
                return True

        # Cache miss
        self.misses += 1

        # Find an empty block in the set
        for block in set_blocks:
            if not block.valid:
                block.valid = True
                block.tag = tag
                block.last_used_time = self.time
                if writeBack:
                    block.writeback = True
                return False

        # Eviction using LRU policy
        lru_block = min(set_blocks, key=lambda b: b.last_used_time)
        if lru_block.writeback:
            self.writebacks += 1
        
        lru_block.valid = True
        lru_block.tag = tag
        lru_block.last_used_time = self.time
        lru_block.writeback = writeBack
        return False

    def get_stats(self):
        """Returns a dictionary of cache statistics."""
        miss_rate = (self.misses / self.total_accesses) if self.total_accesses > 0 else 0
        hit_rate = (self.hits / self.total_accesses) if self.total_accesses > 0 else 0
        return {
            "accesses": self.total_accesses,
            "hits": self.hits,
            "misses": self.misses,
            "writebacks": self.writebacks,
            "hit_rate": f"{hit_rate:.2%}",
            "miss_rate": f"{miss_rate:.2%}"
        }

class MemSimulator:
    """Simulates the entire memory hierarchy."""
    def __init__(self, l1_block_size=16, l2_block_size=16, l1_associativity_type='direct'):
        if l1_block_size not in [4, 8, 16, 32]:
            raise ValueError("L1 Cache block size must be 4, 8, 16, or 32 bytes.")
        if l2_block_size not in [16, 32, 64]:
            raise ValueError("L2 Cache block size must be 16, 32, or 64 bytes.")
        if l1_associativity_type not in ['direct', 'associative']:
            raise ValueError("L1 associativity must be 'direct' or 'associative'.")

        if l1_associativity_type == 'direct':
            l1_assoc = 1
        else: # Fully associative
            l1_assoc = L1_CACHE_SIZE // l1_block_size

        self.l1_instruction_cache = Cache(L1_CACHE_SIZE, l1_block_size, l1_assoc)
        self.l1_data_cache = Cache(L1_CACHE_SIZE, l1_block_size, l1_assoc)
        # L2 is direct-mapped
        self.l2_cache = Cache(L2_CACHE_SIZE, l2_block_size, associativity=1)

    def access_memory(self, address, access_type):
        """
        Simulates a memory access for an instruction fetch, data read, or data write.
        """
        if access_type == 'instruction':
            if not self.l1_instruction_cache.access(address):
                if not self.l2_cache.access(address):
                    # Main memory access (not modeled in detail here)
                    pass
        elif access_type == 'data_read':
            if not self.l1_data_cache.access(address):
                if not self.l2_cache.access(address):
                    # Main memory access
                    pass
        elif access_type == 'data_write':
            if not self.l1_data_cache.access(address, writeBack=True):
                if not self.l2_cache.access(address, writeBack=True):
                    # Main memory access
                    pass

    def get_cost(self):
        """Calculates the cost as per the milestone requirements."""
        total_l1_misses = self.l1_instruction_cache.misses + self.l1_data_cache.misses
        total_l2_misses = self.l2_cache.misses
        # Note: The requirement mentions writebacks, but doesn't specify from which level.
        # Assuming L1 writebacks that miss L2 cause a write to main memory, and L2 writebacks do too.
        total_writebacks = self.l1_instruction_cache.writebacks + self.l1_data_cache.writebacks + self.l2_cache.writebacks
        final_cost = 0.5 * (total_l1_misses + total_l2_misses + total_writebacks)
        return final_cost

    def print_stats(self):
        """Prints detailed statistics for all caches."""
        print("--- L1 Instruction Cache Stats ---")
        for key, value in self.l1_instruction_cache.get_stats().items():
            print(f"{key.capitalize():<12}: {value}")
        
        print("\n--- L1 Data Cache Stats ---")
        for key, value in self.l1_data_cache.get_stats().items():
            print(f"{key.capitalize():<12}: {value}")

        print("\n--- L2 Unified Cache Stats ---")
        for key, value in self.l2_cache.get_stats().items():
            print(f"{key.capitalize():<12}: {value}")
        
        print("\n--- Total Cost ---")
        print(f"Final Cost: {self.get_cost()}")