import pytest
from memory import Block, Cache, MemSimulator

# Test Block Class
def test_block_initialization():
    """Test that a new Block initializes with correct default values."""
    block = Block()
    assert not block.valid
    assert not block.writeback
    assert block.tag == 0
    assert block.last_used_time == 0

# Test Cache Class
@pytest.fixture
def direct_mapped_cache():
    """Provides a direct-mapped cache for testing."""
    # 1KB size, 16-byte blocks, direct-mapped (associativity=1)
    return Cache(size=1024, block_size=16, associativity=1)

@pytest.fixture
def associative_cache():
    """Provides a fully associative cache for testing."""
    # 1KB size, 16-byte blocks, fully associative (64 sets)
    return Cache(size=1024, block_size=16, associativity=64)

def test_cache_initialization(direct_mapped_cache, associative_cache):
    """Test initialization of both direct-mapped and fully associative caches."""
    # Direct-mapped
    assert direct_mapped_cache.size == 1024
    assert direct_mapped_cache.block_size == 16
    assert direct_mapped_cache.associativity == 1
    assert direct_mapped_cache.num_blocks == 64
    assert direct_mapped_cache.num_sets == 64
    assert len(direct_mapped_cache.blocks) == 64

    # Fully associative
    assert associative_cache.size == 1024
    assert associative_cache.block_size == 16
    assert associative_cache.associativity == 64
    assert associative_cache.num_blocks == 64
    assert associative_cache.num_sets == 1
    assert len(associative_cache.blocks) == 1
    assert len(associative_cache.blocks[0]) == 64

def test_cache_access_hit_and_miss(direct_mapped_cache):
    """Test basic cache hit and miss scenarios."""
    # First access should be a miss
    result1 = direct_mapped_cache.access(address=0x100)
    print("First access result:", result1)
    print("Misses:", direct_mapped_cache.misses, "Hits:", direct_mapped_cache.hits)
    assert not result1
    assert direct_mapped_cache.misses == 1
    assert direct_mapped_cache.hits == 0

    # Second access to the same address should be a hit
    assert direct_mapped_cache.access(address=0x100)
    assert direct_mapped_cache.misses == 1
    assert direct_mapped_cache.hits == 1

def test_lru_eviction(associative_cache):
    """Test that the LRU block is evicted when the cache is full."""
    # Fill the cache
    for i in range(64):
        associative_cache.access(address=i * 16)
    
    assert associative_cache.misses == 64

    # Access all but the first block again to make it the LRU
    for i in range(1, 64):
        associative_cache.access(address=i * 16)

    # Access a new block, which should evict the first one (address 0)
    associative_cache.access(address=64 * 16)
    assert associative_cache.misses == 65

    # The original block at address 0 should now be a miss
    assert not associative_cache.access(address=0)
    assert associative_cache.misses == 66

def test_write_back(direct_mapped_cache):
    """Test that a write-back occurs on eviction of a dirty block."""
    # Write to a block, making it dirty
    direct_mapped_cache.access(address=0x200, writeBack=True)
    assert direct_mapped_cache.blocks[32][0].writeback

    # Access another block that maps to the same set, causing eviction
    direct_mapped_cache.access(address=0x200 + 1024)
    assert direct_mapped_cache.writebacks == 1

# Test MemSimulator Class
@pytest.fixture
def mem_simulator():
    """Provides a MemSimulator instance for testing."""
    return MemSimulator(l1_block_size=16, l2_block_size=64, l1_associativity_type='direct')

def test_mem_simulator_initialization(mem_simulator):
    """Test that the memory simulator and its caches are initialized correctly."""
    assert mem_simulator.l1_instruction_cache.block_size == 16
    assert mem_simulator.l1_data_cache.block_size == 16
    assert mem_simulator.l2_cache.block_size == 64
    assert mem_simulator.l1_instruction_cache.associativity == 1

def test_mem_simulator_access(mem_simulator):
    """Test memory access through the simulator."""
    # Instruction fetch miss in L1 and L2
    mem_simulator.access_memory(address=0x1000, access_type='instruction')
    assert mem_simulator.l1_instruction_cache.misses == 1
    assert mem_simulator.l2_cache.misses == 1

    # Subsequent hit in L1
    mem_simulator.access_memory(address=0x1000, access_type='instruction')
    assert mem_simulator.l1_instruction_cache.hits == 1

    # Data read miss
    mem_simulator.access_memory(address=0x2000, access_type='data_read')
    assert mem_simulator.l1_data_cache.misses == 1
    assert mem_simulator.l2_cache.misses == 2

def test_cost_calculation(mem_simulator):
    """Test the cost calculation based on cache statistics."""
    mem_simulator.l1_instruction_cache.misses = 10
    mem_simulator.l1_data_cache.misses = 5
    mem_simulator.l2_cache.misses = 3
    mem_simulator.l1_instruction_cache.writebacks = 2
    mem_simulator.l1_data_cache.writebacks = 1
    mem_simulator.l2_cache.writebacks = 4

    expected_cost = 0.5 * (10 + 5 + 3 + 2 + 1 + 4)
    assert mem_simulator.get_cost() == 12.5
    assert mem_simulator.get_cost() == 12.5

def test_all_passed():
    print("All cache simulator tests passed!")

if __name__ == "__main__":
    import pytest
    pytest.main(["-s", "-v"])


